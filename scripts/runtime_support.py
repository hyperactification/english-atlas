"""Host-neutral discovery for optional native tools and embeddable PDF fonts."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_native_tool(name: str) -> str | None:
    """Explicit environment setting, PATH, then common runtime-relative bins."""
    configured = os.environ.get(name.upper())
    if configured:
        candidate = Path(configured).expanduser()
        resolved = str(candidate) if candidate.is_file() else shutil.which(configured)
        if not resolved:
            raise SystemExit(f"{name.upper()} does not identify an executable: {configured}")
        return resolved
    resolved = shutil.which(name)
    if resolved:
        return resolved
    suffix = ".exe" if os.name == "nt" else ""
    for ancestor in list(Path(sys.executable).resolve().parents)[:3]:
        for directory in ("bin", "Library/bin", "native/poppler/bin", "native/poppler/Library/bin"):
            candidate = ancestor / directory / (name + suffix)
            if candidate.is_file():
                return str(candidate)
    return None


def _font_candidates(role: str) -> list[Path]:
    """Common TrueType families; unsupported CFF collections are skipped later."""
    home = Path.home()
    windir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    directories = [
        windir, Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
        Path("/Library/Fonts"), home / "Library/Fonts", home / ".fonts",
        home / ".local/share/fonts", Path("/usr/share/fonts/truetype"),
        Path("/usr/local/share/fonts"), Path("/usr/share/fonts/opentype"),
    ]
    names = {
        "CN": ["msyh.ttc", "Microsoft YaHei.ttf", "NotoSansSC-Regular.ttf", "NotoSansTC-Regular.ttf", "NotoSansSC[wght].ttf", "NotoSansTC[wght].ttf", "NotoSansCJK-Regular.ttc", "wqy-microhei.ttc", "wqy-zenhei.ttc", "Arial Unicode.ttf", "Arial Unicode MS.ttf", "PingFang.ttc", "STHeiti Light.ttc"],
        "CNB": ["msyhbd.ttc", "Microsoft YaHei Bold.ttf", "NotoSansSC-Bold.ttf", "NotoSansTC-Bold.ttf", "NotoSansSC[wght].ttf", "NotoSansTC[wght].ttf", "NotoSansCJK-Bold.ttc", "wqy-microhei.ttc", "wqy-zenhei.ttc", "STHeiti Medium.ttc"],
        "EN": ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf"],
        "ENB": ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf"],
    }[role]
    candidates = [directory / filename for filename in names for directory in directories]
    # Linux distributions normally put font families in subdirectories.
    for directory in directories:
        if directory.is_dir() and directory != windir:
            for filename in names:
                candidates.extend(directory.glob("**/" + filename))
    fc_match = shutil.which("fc-match")
    if fc_match:
        family = "sans-serif:lang=zh-cn" if role.startswith("CN") else "sans-serif"
        if role.endswith("B"):
            family += ":weight=bold"
        try:
            result = subprocess.run([fc_match, "--format=%{file}", family], capture_output=True, text=True, timeout=10, check=True)
            if result.stdout.strip():
                candidates.append(Path(result.stdout.strip()))
        except (OSError, subprocess.SubprocessError):
            pass
    return list(dict.fromkeys(candidates))


def cjk_characters(value: object) -> set[str]:
    """Check text coverage before embedding rather than emitting empty glyphs."""
    if isinstance(value, dict):
        return set().union(*(cjk_characters(v) for v in value.values()), set())
    if isinstance(value, list):
        return set().union(*(cjk_characters(v) for v in value), set())
    if not isinstance(value, str):
        return set()
    return {c for c in value if "\u3400" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f" or "\uff01" <= c <= "\uff60"}


def text_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_values(item)
    elif isinstance(value, str):
        yield value


def register_pdf_fonts(args, book: dict) -> dict:
    """Register four renderer font aliases using explicit settings or discovery."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont, TTFError

    texts = list(text_values(book))
    # Include punctuation, arrows, math signs and other non-CJK text as well.
    # Variation selectors are shaping hints rather than independent glyphs.
    printable = lambda c: c.isprintable() and not ("\ufe00" <= c <= "\ufe0f")
    symbols = "≠→·“”‘’–—…•｜"
    required = {c for text in texts for c in text if printable(c)} | set(symbols + "来源原文页精讀續頁英語圖譜詞彙中文繁體简体")
    english_required = {c for text in texts if not cjk_characters(text) for c in text if printable(c)} | set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + symbols.replace("｜", ""))
    overrides = {
        "CN": (args.font_cn, "ENGLISH_ATLAS_FONT_CN"),
        "CNB": (args.font_cn_bold, "ENGLISH_ATLAS_FONT_CN_BOLD"),
        "EN": (args.font_en, "ENGLISH_ATLAS_FONT_EN"),
        "ENB": (args.font_en_bold, "ENGLISH_ATLAS_FONT_EN_BOLD"),
    }
    selected = {}
    for alias in ("CN", "CNB", "EN", "ENB"):
        cli, variable = overrides[alias]
        configured = cli or os.environ.get(variable)
        candidates = [Path(configured).expanduser()] if configured else _font_candidates(alias)
        # A missing bold family may reuse the matching regular family. Reusing
        # a CJK family for English is the last resort and keeps words intact.
        if not configured:
            fallback = {"CNB": "CN", "EN": "CN", "ENB": "EN"}.get(alias)
            if fallback in selected:
                candidates.append(Path(selected[fallback]["path"]))
        diagnostics = []
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                font = TTFont(alias, str(candidate), subfontIndex=0)
                needed = required if alias.startswith("CN") else english_required
                missing = sorted(c for c in needed if ord(c) not in font.face.charToGlyph)
                if missing:
                    diagnostics.append(f"{candidate}: missing characters " + ", ".join(f"{c} (U+{ord(c):04X})" for c in missing[:12]))
                    continue
                pdfmetrics.registerFont(font)
                selected[alias] = {"path": str(candidate.resolve()), "family": font.face.familyName.decode("utf-8", "replace") if isinstance(font.face.familyName, bytes) else str(font.face.familyName)}
                break
            except (TTFError, OSError, ValueError) as exc:
                diagnostics.append(f"{candidate}: {exc}")
        else:
            flag = {"CN": "--font-cn", "CNB": "--font-cn-bold", "EN": "--font-en", "ENB": "--font-en-bold"}[alias]
            detail = "\n".join(diagnostics[:5]) or "No candidate font file was found."
            raise SystemExit(f"No usable {alias} font. Set {flag} or {variable} to a TrueType-outline TTF or compatible TTC with the required characters. OpenType/CFF fonts are not supported by this PDF renderer.\n{detail}")
    for family, bold in (("CN", "CNB"), ("EN", "ENB")):
        pdfmetrics.registerFontFamily(family, normal=family, bold=bold, italic=family, boldItalic=bold)
    return selected
