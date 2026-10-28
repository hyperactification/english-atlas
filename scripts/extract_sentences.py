#!/usr/bin/env python3
"""Extract numbered English exercises without silently repairing their text.

Usage: python extract_sentences.py --input source.pdf --output-dir work/extracted

Exit 0: extraction passed automatic checks. Exit 2: inspect the report (including
OCR needs or suspected annotations) before authoring. Exit 1: extraction failed.
Only clearly marked parenthetical glosses are removed from ``english``; ``raw``
and source.txt retain the source wording. No OCR or translation is performed.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata
from runtime_support import find_native_tool


NUMBERED = re.compile(r"^\s*([0-9０-９]{1,6})[.．、)）]\s*(.*)$")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
WORD = re.compile(r"[A-Za-z]+")
# Explicit POS markers keep ordinary parenthetical source content intact.
GLOSS_START = re.compile(
    r"^\s*(?:(?:adj|adv|vt|vi|v|n|pron|prep|conj|num|aux|det|interj|art)\s*\."
    r"|(?:名词|动词|形容词|副词|代词|介词|连词|数词|助动词|感叹词|词义|释义|意为|译为)\s*[：:]?)",
    re.IGNORECASE,
)
OPEN_TO_CLOSE = {"(": ")", "（": "）"}
CLOSE_TO_OPEN = {v: k for k, v in OPEN_TO_CLOSE.items()}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def locate_pdftotext() -> str | None:
    """Use PDFTOTEXT, PATH, or an adjacent native-tool installation."""
    return find_native_tool("pdftotext")


def split_pages(text: str) -> list[str]:
    pages = text.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    # pdftotext terminates every page, including the last, with a form feed.
    if len(pages) > 1 and not pages[-1].strip():
        pages.pop()
    return pages or [""]


def extract_pdf(path: Path, warnings: list[dict]) -> tuple[str, list[str], str]:
    pdftotext = locate_pdftotext()
    if pdftotext:
        try:
            result = subprocess.run(
                [pdftotext, "-layout", "-enc", "UTF-8", str(path), "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=120,
            )
            text = result.stdout.decode("utf-8", errors="strict")
            if result.stderr.strip():
                warnings.append({
                    "code": "pdftotext_diagnostic",
                    "message": result.stderr.decode("utf-8", errors="replace").strip()[:2000],
                })
            return text, split_pages(text), "pdftotext"
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
            warnings.append({"code": "pdftotext_failed", "message": str(exc)[:1000]})
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction requires pdftotext on PATH (or PDFTOTEXT), or the pypdf package. "
            "Use the bundled runtime when available."
        ) from exc
    reader = PdfReader(str(path))
    if reader.is_encrypted and not reader.decrypt(""):
        raise RuntimeError("The PDF is encrypted; provide a readable copy.")
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # One bad page must remain visible in the report.
            pages.append("")
            warnings.append({"code": "page_extraction_failed", "page": index, "message": str(exc)[:1000]})
    return "\f".join(pages), pages, "pypdf"


def margin_key(line: str, page: int, page_count: int) -> str:
    value = compact(line)
    # Normalize an explicit page counter, not arbitrary numbers inside a title.
    value = re.sub(r"\bpage\s+\d+(?:\s*(?:of|/)\s*\d+)?\b", "page #", value, flags=re.I)
    value = re.sub(r"第\s*\d+\s*页(?:\s*[/／]\s*共?\s*\d+\s*页)?", "第#页", value)
    # pypdf may collapse the footer gap to one space and emit it near the page
    # header. Only a counter matching this actual page is normalized; removal
    # still requires the same edge pattern on at least half the document pages.
    tail = re.search(r"\s+(\d+)\s*$", line)
    if tail and int(tail.group(1)) == page:
        value = compact(line[:tail.start()]) + " #"
    return value


def repeated_margins(pages: list[str]) -> tuple[set[tuple[int, int]], list[dict]]:
    """Remove only repeated edge lines, and report every inferred removal."""
    candidates: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for page_num, page in enumerate(pages, start=1):
        lines = page.splitlines()
        nonempty = [(i, line) for i, line in enumerate(lines) if line.strip()]
        for side, edges in (("header", nonempty[:2]), ("footer", nonempty[-2:])):
            for line_num, line in edges:
                if NUMBERED.match(line):
                    continue
                key = margin_key(line, page_num, len(pages))
                if key:
                    candidates[(side, key)].append((page_num, line_num, line))
    removed: set[tuple[int, int]] = set()
    details: list[dict] = []
    # Two-page files still support repeated-margin detection. For longer files,
    # require presence on at least half the pages rather than any repeated line.
    threshold = max(2, math.ceil(len(pages) / 2))
    for (side, key), occurrences in candidates.items():
        seen_pages = sorted({page for page, _, _ in occurrences})
        if len(seen_pages) >= threshold:
            for page_num, line_num, _ in occurrences:
                removed.add((page_num, line_num))
            details.append({"position": side, "normalized_text": key, "pages": seen_pages})
    return removed, details


def is_page_number(line: str, page: int, edge: bool) -> bool:
    if not edge:
        return False
    stripped = line.strip()
    for pattern in (
        r"(?:Page\s+)?(\d+)(?:\s*(?:/|of)\s*\d+)?",
        r"第\s*(\d+)\s*页(?:\s*[/／]\s*共?\s*\d+\s*页)?",
    ):
        match = re.fullmatch(pattern, stripped, flags=re.I)
        if match and int(match.group(1)) == page:
            return True
    return False


def remove_glosses(raw: str) -> tuple[str, list[str], list[str]]:
    """Balanced nested parentheses, with conservative gloss classification.

    A Chinese-bearing span is removed only when it starts with an explicit POS
    marker or gloss label. An English parenthesis containing a nested gloss is
    retained, with only its recognizable inner gloss removed. Unknown Chinese
    annotations and unbalanced delimiters remain available for human review.
    """
    stack: list[tuple[str, int]] = []
    spans: list[tuple[int, int]] = []
    issues: list[str] = []
    for index, char in enumerate(raw):
        if char in OPEN_TO_CLOSE:
            stack.append((char, index))
        elif char in CLOSE_TO_OPEN:
            if stack and stack[-1][0] == CLOSE_TO_OPEN[char]:
                _, start = stack.pop()
                inner = raw[start + 1:index]
                if CJK.search(inner) and GLOSS_START.match(inner):
                    spans.append((start, index + 1))
            else:
                issues.append("unbalanced_parentheses")
    if stack:
        issues.append("unbalanced_parentheses")
    # An outer gloss can contain an inner gloss; remove the outer span once.
    maximal: list[tuple[int, int]] = []
    for start, end in sorted(spans, key=lambda item: (item[0], -item[1])):
        if maximal and start >= maximal[-1][0] and end <= maximal[-1][1]:
            continue
        maximal.append((start, end))
    cursor = 0
    pieces: list[str] = []
    removed: list[str] = []
    for start, end in maximal:
        pieces.append(raw[cursor:start])
        # Keep word boundaries when an annotation was adjacent to both words.
        pieces.append(" ")
        removed.append(raw[start:end])
        cursor = end
    pieces.append(raw[cursor:])
    english = compact("".join(pieces))
    english = re.sub(r"\s+([,.;:!?])", r"\1", english)
    if CJK.search(english):
        issues.append("unresolved_chinese_text")
    if re.search(r"[A-Za-z]-\s*\n\s*[A-Za-z]", raw):
        issues.append("possible_line_end_hyphen")
    if "\ufffd" in raw or "\x00" in raw:
        issues.append("suspected_extraction_damage")
    return english, removed, sorted(set(issues))


def parse_sentences(pages: list[str], warnings: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    margin_positions, margin_details = repeated_margins(pages)
    entries: list[dict] = []
    gloss_details: list[dict] = []
    current: dict | None = None
    body: list[str] = []

    def finish() -> None:
        nonlocal current, body
        if current is None:
            return
        raw = "\n".join(body).strip()
        english, glosses, issues = remove_glosses(raw)
        entry = {"id": current["id"], "page": current["page"], "raw": raw, "english": english}
        entries.append(entry)
        for gloss in glosses:
            gloss_details.append({"id": entry["id"], "page": entry["page"], "text": gloss})
        for code in issues:
            warnings.append({
                "code": code,
                "id": entry["id"],
                "page": entry["page"],
                "message": {
                    "unresolved_chinese_text": "Chinese text remains; inspect it rather than deleting characters indiscriminately.",
                    "unbalanced_parentheses": "A parenthesis is unbalanced or mismatched; no repair was invented.",
                    "possible_line_end_hyphen": "Check whether the line-end hyphen belongs to the English word.",
                    "suspected_extraction_damage": "Replacement or null characters suggest damaged text extraction.",
                }[code],
                "excerpt": english[:300],
            })
        if not english or len(WORD.findall(english)) < 3:
            warnings.append({"code": "short_sentence", "id": entry["id"], "page": entry["page"],
                             "message": "The numbered item contains fewer than three English words; verify its boundary.",
                             "excerpt": english})
        current, body = None, []

    for page_num, page in enumerate(pages, start=1):
        lines = page.splitlines()
        nonempty = [i for i, line in enumerate(lines) if line.strip()]
        edges = set(nonempty[:2] + nonempty[-2:])
        for line_num, line in enumerate(lines):
            if (page_num, line_num) in margin_positions:
                continue
            if is_page_number(line, page_num, line_num in edges):
                continue
            match = NUMBERED.match(line)
            if match:
                identifier = int(match.group(1))
                if identifier <= 0:
                    warnings.append({"code": "nonpositive_id", "page": page_num,
                                     "message": "A zero item number was not accepted as a sentence ID.", "excerpt": line.strip()})
                    continue
                finish()
                current = {"id": identifier, "page": page_num}
                body = [match.group(2).strip()]
            elif current is not None and line.strip():
                body.append(line.strip())
            # Text before the first numbered sentence is a preamble, not item 0.
    finish()
    return entries, margin_details, gloss_details


def run(input_path: Path, output_dir: Path) -> dict:
    warnings: list[dict] = []
    input_path = input_path.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        text, pages, method = extract_pdf(input_path, warnings)
    elif suffix == ".txt":
        text = input_path.read_text(encoding="utf-8-sig", errors="strict")
        pages, method = split_pages(text), "utf8_text"
    else:
        raise ValueError("--input must be a PDF or UTF-8 TXT file.")
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "source.txt").write_text(text, encoding="utf-8")
    stats = []
    ocr_pages = []
    for page_num, page in enumerate(pages, start=1):
        printable = sum(not char.isspace() for char in page)
        latin_letters = sum(char.isascii() and char.isalpha() for char in page)
        stats.append({"page": page_num, "nonspace_characters": printable, "latin_letters": latin_letters})
        if suffix == ".pdf" and (printable < 40 or latin_letters < 20):
            ocr_pages.append(page_num)
            warnings.append({"code": "low_text_page", "page": page_num,
                             "message": "Too little extractable text. OCR or visual confirmation of an intentionally blank/title page is required."})
    entries, removed_margins, removed_glosses = parse_sentences(pages, warnings)
    ids = [item["id"] for item in entries]
    counts = Counter(ids)
    duplicates = sorted(identifier for identifier, count in counts.items() if count > 1)
    missing = sorted(set(range(min(ids), max(ids) + 1)) - set(ids)) if ids else []
    out_of_order = [ids[i] for i in range(1, len(ids)) if ids[i] < ids[i - 1]]
    if duplicates:
        warnings.append({"code": "duplicate_ids", "message": "Repeated item numbers were retained, not overwritten.", "ids": duplicates})
    if missing:
        warnings.append({"code": "missing_ids", "message": "Numbers are missing between the first and last extracted ID. No sentences were invented.", "ids": missing})
    if out_of_order:
        warnings.append({"code": "out_of_order_ids", "message": "Numbering moves backwards; inspect section restarts or extraction order.", "ids": out_of_order})
    if not entries:
        warnings.append({"code": "no_numbered_sentences", "message": "No numbered sentences were recognized. Use OCR or inspect the numbering/layout manually."})
    status = "needs_ocr" if ocr_pages else "needs_review" if warnings else "ok"
    report = {
        "schema_version": 1,
        "input": str(input_path),
        "input_type": suffix[1:],
        "method": method,
        "status": status,
        "needs_ocr": bool(ocr_pages),
        "ocr_pages": ocr_pages,
        "page_count": len(pages),
        "page_text_stats": stats,
        "sentences_extracted": len(entries),
        "ids": ids,
        "duplicate_ids": duplicates,
        "missing_ids": missing,
        "out_of_order_ids": out_of_order,
        "removed_repeated_margins": removed_margins,
        "removed_glosses": removed_glosses,
        "warnings": warnings,
    }
    write_json(output_dir / "sentences.json", entries)
    write_json(output_dir / "extraction_report.json", report)
    return report


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Numbered exercise PDF or UTF-8 TXT")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.input, args.output_dir)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in
                      ("status", "method", "page_count", "sentences_extracted", "needs_ocr")}, ensure_ascii=False))
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
