"""Convert structured vocabulary notes into lossless, readable plain text.

Legacy strings remain unchanged. Authored objects are validated by
validate_content.py before rendering; this helper does not invent synonyms.
"""

from __future__ import annotations


def format_vocabulary_item(item: str | dict) -> str:
    """Keep lexical content in strings usable by PDF, HTML and text QA."""
    if isinstance(item, str):
        return item
    synonyms = item["near_synonyms"]
    lines = [f'{item["term"]}：{item["explanation"]}']
    lines.append("Near synonyms: " + (" / ".join(s["text"] for s in synonyms) or "—"))
    for synonym in synonyms:
        lines.append(f'Usage note: {synonym["text"]} — {synonym["distinction"]}')
    if item.get("no_synonym_reason"):
        lines.append("Usage note: " + item["no_synonym_reason"])
    return "\n".join(lines)


def format_vocabulary(items: list[str | dict]) -> list[str]:
    return [format_vocabulary_item(item) for item in items]
