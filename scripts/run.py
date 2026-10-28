#!/usr/bin/env python3
"""Portable English Atlas command dispatcher. Requires Python 3.10 or newer."""
from __future__ import annotations

import argparse
from importlib import metadata, util
import json
import os
from pathlib import Path
import subprocess
import sys

SCRIPTS = {"extract": "extract_sentences.py", "validate": "validate_content.py", "render": "render_notes.py", "verify": "verify_artifacts.py"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", *SCRIPTS])
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="Arguments forwarded unchanged to the selected script")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if args.action == "doctor":
        from runtime_support import find_native_tool
        packages = {}
        for module, distribution in (("reportlab", "reportlab"), ("pypdf", "pypdf"), ("PIL", "Pillow")):
            available = util.find_spec(module) is not None
            try:
                version = metadata.version(distribution) if available else None
            except metadata.PackageNotFoundError:
                version = "unknown"
            packages[distribution] = {"available": available, "version": version}
        result = {"python": sys.executable, "python_version": sys.version.split()[0], "platform": sys.platform, "packages": packages, "optional_tools": {name: find_native_tool(name) for name in ("pdftotext", "pdftoppm")}, "font_check": "Fonts are checked against actual content during rendering; use --font-cn or ENGLISH_ATLAS_FONT_CN if discovery cannot find an embeddable CJK font."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if all(package["available"] for package in packages.values()) else 1
    environment = os.environ.copy()
    environment.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.call([sys.executable, str(Path(__file__).resolve().parent / SCRIPTS[args.action]), *args.arguments], env=environment)


if __name__ == "__main__":
    raise SystemExit(main())
