"""Extract and parse JavaDoc comments from tree-sitter nodes."""
from __future__ import annotations
import re
from typing import Optional
from tree_sitter import Node


def extract_javadoc(node: Node) -> Optional[dict]:
    """
    Find the JavaDoc comment (/** ... */) immediately preceding the given node
    among its siblings, and parse it into structured form.
    Returns None if no JavaDoc found.
    """
    raw = _find_preceding_javadoc(node)
    if raw is None:
        return None
    return _parse_javadoc(raw)


def _find_preceding_javadoc(node: Node) -> Optional[str]:
    parent = node.parent
    if parent is None:
        return None

    prev = None
    for child in parent.children:
        if child.id == node.id:
            break
        prev = child

    if prev is not None and prev.type == "block_comment":
        text = prev.text.decode("utf-8")
        if text.startswith("/**"):
            return text
    return None


def _parse_javadoc(raw: str) -> dict:
    # Strip /** and */
    inner = raw.strip()
    if inner.startswith("/**"):
        inner = inner[3:]
    if inner.endswith("*/"):
        inner = inner[:-2]

    # Clean leading * on each line
    lines = []
    for line in inner.splitlines():
        line = line.strip()
        if line.startswith("*"):
            line = line[1:].strip()
        lines.append(line)

    text = "\n".join(lines).strip()

    # Split into description and tags sections
    tag_pattern = re.compile(r'(?m)^(@\w+|\{@\w+)')
    tag_start = tag_pattern.search(text)

    if tag_start:
        description = text[:tag_start.start()].strip()
        tags_text = text[tag_start.start():]
    else:
        description = text.strip()
        tags_text = ""

    tags = _parse_tags(tags_text) if tags_text else {}

    result = {"raw": raw, "description": description}
    if tags:
        result["tags"] = tags
    return result


def _parse_tags(tags_text: str) -> dict:
    # Split on tag boundaries
    tag_re = re.compile(r'(?m)^(@\w+|\{@\w+[^}]*\})(.*?)(?=(?m)^(?:@\w+|\{@\w+)|\Z)', re.DOTALL)
    # Simpler: split lines and group by tag
    lines = tags_text.splitlines()

    tags: dict = {}
    current_tag = None
    current_content: list[str] = []

    def flush():
        if current_tag is None:
            return
        content = " ".join(current_content).strip()
        _add_tag(tags, current_tag, content)

    for line in lines:
        line = line.strip()
        m = re.match(r'^@(\w+)\s*(.*)', line)
        if m:
            flush()
            current_tag = m.group(1)
            current_content = [m.group(2).strip()]
        elif line:
            if current_tag:
                current_content.append(line)

    flush()
    return tags


def _add_tag(tags: dict, tag: str, content: str):
    if tag == "param":
        parts = content.split(None, 1)
        entry = {"name": parts[0], "description": parts[1].strip() if len(parts) > 1 else ""}
        tags.setdefault("param", []).append(entry)
    elif tag in ("throws", "exception"):
        parts = content.split(None, 1)
        entry = {"type": parts[0], "description": parts[1].strip() if len(parts) > 1 else ""}
        tags.setdefault("throws", []).append(entry)
    elif tag == "see":
        tags.setdefault("see", []).append(content)
    elif tag == "author":
        tags.setdefault("author", []).append(content)
    elif tag in ("return", "since", "deprecated", "version"):
        tags[tag] = content
    else:
        # Store other tags as-is
        tags.setdefault(tag, []).append(content)
