#!/usr/bin/env python3
"""Validate study-note content, source fidelity, grouping, and diagram labels.

Usage: python validate_content.py --input notes.json --source sentences.json
Optional: --report validation_report.json. Exit 0 means valid; exit 1 means the
content or input is invalid. This checks structure/fidelity, not translation
quality or rendered layout. Empty source_note and group warning are permitted.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


def normalized(text: str) -> str:
    """Ignore layout whitespace, but do not normalize away textual differences."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def source_fragment(fragment: str, sentence: str) -> bool:
    """Allow intentional ellipses, but reject invented words or changed tense."""
    pieces = [normalized(piece) for piece in re.split(r"\.{3}|…", fragment)]
    pieces = [piece for piece in pieces if piece]
    if not pieces:
        return False
    cursor = 0
    for piece in pieces:
        expression = re.escape(piece)
        if piece[0].isalnum():
            expression = r"(?<!\w)" + expression
        if piece[-1].isalnum():
            expression += r"(?!\w)"
        match = re.search(expression, sentence[cursor:])
        if not match:
            return False
        cursor += match.end()
    return True


class Validator:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def error(self, path: str, message: str, code: str = "invalid_field") -> None:
        self.errors.append({"path": path, "code": code, "message": message})

    def warn(self, path: str, message: str, code: str = "review_required") -> None:
        self.warnings.append({"path": path, "code": code, "message": message})

    def string(self, value: object, path: str, allow_empty: bool = False) -> bool:
        if not isinstance(value, str) or (not allow_empty and not value.strip()):
            self.error(path, "Expected a non-empty string." if not allow_empty else "Expected a string; empty is allowed.")
            return False
        if "\ufffd" in value or "\x00" in value:
            self.error(path, "Replacement or null characters suggest corrupted text.", "corrupt_text")
        return True

    def strings(self, value: object, path: str) -> None:
        if not isinstance(value, list) or not value:
            self.error(path, "Expected a non-empty array of strings.")
            return
        for index, item in enumerate(value):
            self.string(item, f"{path}[{index}]")

    def triples(self, value: object, path: str, count: int | None = None) -> None:
        if not isinstance(value, list) or not value:
            self.error(path, "Expected a non-empty array of three-string rows.")
            return
        if count is not None and len(value) != count:
            self.error(path, f"Expected exactly {count} rows, got {len(value)}.")
        for index, row in enumerate(value):
            if not isinstance(row, list) or len(row) != 3:
                self.error(f"{path}[{index}]", "Expected exactly three strings.")
            else:
                for col, cell in enumerate(row):
                    self.string(cell, f"{path}[{index}][{col}]")

    def validate(self, data: object, source: object | None = None) -> dict:
        if not isinstance(data, dict):
            self.error("$", "Top-level notes JSON must be an object.")
            return self.result(0, 0, 0)
        meta = data.get("meta")
        if not isinstance(meta, dict):
            self.error("meta", "Expected an object.")
            meta = {}
        for field in ("title", "chapter", "source_name"):
            self.string(meta.get(field), f"meta.{field}")
        source_pages = meta.get("source_pages")
        if not positive_int(source_pages):
            self.error("meta.source_pages", "Expected the positive integer number of original source pages.")

        entries = data.get("entries")
        if not isinstance(entries, list) or not entries:
            self.error("entries", "Expected a non-empty array.")
            entries = []
        ids: list[int] = []
        by_id: dict[int, dict] = {}
        for index, entry in enumerate(entries):
            path = f"entries[{index}]"
            if not isinstance(entry, dict):
                self.error(path, "Expected an object.")
                continue
            identifier = entry.get("id")
            if not positive_int(identifier):
                self.error(path + ".id", "Expected an original positive integer item number.")
            else:
                ids.append(identifier)
                by_id[identifier] = entry
            page = entry.get("page")
            if not positive_int(page):
                self.error(path + ".page", "Expected a positive original source page number.")
            elif positive_int(source_pages) and page > source_pages:
                self.error(path + ".page", "Page exceeds meta.source_pages.", "invalid_source_page")
            for field in ("english", "translation", "keyword", "memory_tip"):
                self.string(entry.get(field), path + "." + field)
            self.string(entry.get("source_note"), path + ".source_note", allow_empty=True)
            for field in ("structure", "vocabulary", "exam_points", "pitfalls"):
                self.strings(entry.get(field), path + "." + field)
            diagram = entry.get("diagram")
            if not isinstance(diagram, list) or not diagram:
                self.error(path + ".diagram", "Expected a non-empty array of role/text objects.")
            else:
                for node_index, node in enumerate(diagram):
                    node_path = f"{path}.diagram[{node_index}]"
                    if not isinstance(node, dict):
                        self.error(node_path, "Expected an object.")
                        continue
                    role = node.get("role")
                    if self.string(role, node_path + ".role"):
                        if not role.isascii() or not re.search(r"[A-Za-z]", role):
                            self.error(node_path + ".role", "Use an English label, e.g. Subject or Infinitive of purpose.", "nonenglish_grammar_label")
                    text = node.get("text")
                    if self.string(text, node_path + ".text") and isinstance(entry.get("english"), str):
                        if not source_fragment(text, normalized(entry["english"])):
                            self.error(node_path + ".text", "Diagram text is not an ordered fragment of this original English sentence. Use ellipses only for omissions.", "diagram_not_source")
        duplicates = sorted(identifier for identifier, count in Counter(ids).items() if count > 1)
        if duplicates:
            self.error("entries", f"Duplicate IDs: {duplicates}", "duplicate_ids")
        if ids != sorted(ids):
            self.error("entries", "Entries are not in increasing original-ID order.", "out_of_order_ids")

        if source is not None:
            self.check_source(source, entries, by_id, ids, source_pages)
        elif ids:
            gaps = sorted(set(range(min(ids), max(ids) + 1)) - set(ids))
            if gaps:
                self.error("entries", f"Unexplained numbering gaps: {gaps}. Supply --source if the original itself has gaps.", "missing_ids")

        groups = data.get("groups")
        if not isinstance(groups, list) or not groups:
            self.error("groups", "Expected a non-empty array.")
            groups = []
        coverage = Counter({identifier: 0 for identifier in ids})
        for index, group in enumerate(groups):
            path = f"groups[{index}]"
            if not isinstance(group, dict):
                self.error(path, "Expected an object.")
                continue
            for field in ("title", "subtitle", "focus"):
                self.string(group.get(field), path + "." + field)
            self.string(group.get("warning"), path + ".warning", allow_empty=True)
            if "icon" in group:
                self.string(group["icon"], path + ".icon")
            self.triples(group.get("nodes"), path + ".nodes", count=3)
            self.triples(group.get("rows"), path + ".rows")
            interval = group.get("range")
            if not isinstance(interval, list) or len(interval) != 2 or not all(positive_int(v) for v in interval):
                self.error(path + ".range", "Expected [first_id, last_id], both positive integers.")
            elif interval[0] > interval[1]:
                self.error(path + ".range", "Range starts after it ends.")
            else:
                if interval[0] not in by_id or interval[1] not in by_id:
                    self.error(path + ".range", "Both range endpoints must be real entry IDs.", "unknown_group_endpoint")
                covered = [identifier for identifier in coverage if interval[0] <= identifier <= interval[1]]
                if not covered:
                    self.error(path + ".range", "This group covers no entries.", "empty_group")
                for identifier in covered:
                    coverage[identifier] += 1
        missing_groups = [identifier for identifier, count in coverage.items() if count == 0]
        overlapping_groups = [identifier for identifier, count in coverage.items() if count > 1]
        if missing_groups:
            self.error("groups", f"IDs not covered by any group: {missing_groups}", "group_coverage_missing")
        if overlapping_groups:
            self.error("groups", f"IDs covered by more than one group: {overlapping_groups}", "group_coverage_overlap")

        glossary = data.get("glossary")
        if not isinstance(glossary, list) or not glossary:
            self.error("glossary", "Expected a non-empty array.")
            glossary = []
        for index, item in enumerate(glossary):
            path = f"glossary[{index}]"
            if not isinstance(item, dict):
                self.error(path, "Expected an object.")
                continue
            for field in ("term", "translation", "explanation"):
                self.string(item.get(field), path + "." + field)
            examples = item.get("examples")
            if not isinstance(examples, list) or not examples:
                self.error(path + ".examples", "Expected at least one real entry ID.")
            else:
                for j, identifier in enumerate(examples):
                    if not positive_int(identifier) or identifier not in by_id:
                        self.error(f"{path}.examples[{j}]", f"Unknown or invalid example ID: {identifier!r}", "unknown_glossary_example")
        return self.result(len(entries), len(groups), len(glossary))

    def check_source(self, source: object, entries: list, by_id: dict, ids: list,
                     source_pages: object) -> None:
        if not isinstance(source, list) or not source:
            self.error("source", "Source JSON must be a non-empty array of extracted sentences.")
            return
        source_by_id = {}
        source_ids = []
        for index, item in enumerate(source):
            path = f"source[{index}]"
            if not isinstance(item, dict):
                self.error(path, "Expected an object.")
                continue
            if not positive_int(item.get("id")):
                self.error(path + ".id", "Expected a positive integer ID.")
                continue
            source_ids.append(item["id"])
            source_by_id[item["id"]] = item
            self.string(item.get("english"), path + ".english")
            if not positive_int(item.get("page")):
                self.error(path + ".page", "Expected a positive source page.")
            elif positive_int(source_pages) and item["page"] > source_pages:
                self.error("meta.source_pages", f"Too small for source page {item['page']}.", "invalid_source_page_count")
        source_duplicates = sorted(identifier for identifier, count in Counter(source_ids).items() if count > 1)
        if source_duplicates:
            self.error("source", f"Source IDs are ambiguous because they repeat: {source_duplicates}", "duplicate_source_ids")
        missing = sorted(set(source_ids) - set(ids))
        extra = sorted(set(ids) - set(source_ids))
        if missing:
            self.error("entries", f"Missing source IDs: {missing}", "missing_source_entries")
        if extra:
            self.error("entries", f"IDs absent from source: {extra}", "invented_entries")
        if not missing and not extra and not source_duplicates and ids != source_ids:
            self.error("entries", "Entry order does not match source order.", "source_order_mismatch")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not positive_int(entry.get("id")):
                continue
            original = source_by_id.get(entry["id"])
            if original is None:
                continue
            path = f"entries[{index}]"
            english, original_english = entry.get("english"), original.get("english")
            if isinstance(english, str) and isinstance(original_english, str):
                if normalized(english) != normalized(original_english):
                    self.error(path + ".english", f"English differs from original source ID {entry['id']}. Put suggested rewrites in source_note, not in the original.", "source_english_mismatch")
            if entry.get("page") != original.get("page"):
                self.error(path + ".page", f"Original source ID {entry['id']} is on page {original.get('page')!r}.", "source_page_mismatch")
        if source_ids:
            gaps = sorted(set(range(min(source_ids), max(source_ids) + 1)) - set(source_ids))
            if gaps:
                self.warn("source", f"Source numbering itself has gaps: {gaps}. The validator does not invent missing sentences.", "source_numbering_gaps")

    def result(self, entries: int, groups: int, glossary: int) -> dict:
        return {
            "valid": not self.errors,
            "entry_count": entries,
            "group_count": groups,
            "glossary_count": glossary,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "verification_boundary": "Schema, coverage, source wording/pages, diagram fragments and labels; not translation accuracy or rendered layout.",
        }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Authored notes.json")
    parser.add_argument("--source", type=Path, help="Original sentences.json from the extractor")
    parser.add_argument("--report", type=Path, help="Optional JSON validation report")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        source = json.loads(args.source.read_text(encoding="utf-8-sig")) if args.source else None
        report = Validator().validate(data, source)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"valid": False, "error_count": 1, "errors": [{"path": "$", "code": "input_error", "message": str(exc)}]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
