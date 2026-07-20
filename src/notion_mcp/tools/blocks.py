import re

from ..client import get, patch, delete

# Notion caps each rich_text segment's text.content at 2000 characters.
_MAX_RICH_TEXT_LEN = 2000


def _text_segment(content: str, bold: bool = False, italic: bool = False, code: bool = False) -> dict:
    return {
        "type": "text",
        "text": {"content": content},
        "annotations": {
            "bold": bold,
            "italic": italic,
            "code": code,
            "strikethrough": False,
            "underline": False,
            "color": "default",
        },
    }


def _text_chunks(content: str, bold: bool = False, italic: bool = False, code: bool = False) -> list[dict]:
    if not content:
        return [_text_segment("", bold, italic, code)]
    return [
        _text_segment(content[i : i + _MAX_RICH_TEXT_LEN], bold, italic, code)
        for i in range(0, len(content), _MAX_RICH_TEXT_LEN)
    ]


def _parse_inline(text: str) -> list[dict]:
    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)", text)
    rich_text = []
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            rich_text.extend(_text_chunks(part[1:-1], code=True))
        elif part.startswith("**") and part.endswith("**"):
            rich_text.extend(_text_chunks(part[2:-2], bold=True))
        elif (part.startswith("*") and part.endswith("*")) or (part.startswith("_") and part.endswith("_")):
            rich_text.extend(_text_chunks(part[1:-1], italic=True))
        else:
            rich_text.extend(_text_chunks(part))
    return rich_text


def _paragraph(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _parse_inline(text)}}


def _heading(level: int, text: str) -> dict:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": _parse_inline(text)}}


def _bulleted(text: str) -> dict:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _parse_inline(text)}}


def _numbered(text: str) -> dict:
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": _parse_inline(text)}}


def _todo(text: str, checked: bool) -> dict:
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": _parse_inline(text), "checked": checked}}


def _quote(text: str) -> dict:
    return {"object": "block", "type": "quote", "quote": {"rich_text": _parse_inline(text)}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _code(text: str, language: str = "plain text") -> dict:
    return {"object": "block", "type": "code", "code": {"rich_text": _text_chunks(text), "language": language}}


_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
_TABLE_SEP_RE = re.compile(r"^\|?[\s:|-]+\|?$")


def _split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _table(rows: list[list[str]]) -> dict:
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": [
                {"object": "block", "type": "table_row", "table_row": {"cells": [_parse_inline(cell) for cell in row]}}
                for row in normalized
            ],
        },
    }


def markdown_to_blocks(markdown: str) -> list[dict]:
    lines = markdown.split("\n")
    blocks: list[dict] = []
    paragraph_buffer: list[str] = []

    def flush_paragraph():
        if paragraph_buffer:
            blocks.append(_paragraph("\n".join(paragraph_buffer)))
            paragraph_buffer.clear()

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip() or "plain text"
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append(_code("\n".join(code_lines), language))
            i += 1
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            blocks.append(_heading(len(heading_match.group(1)), heading_match.group(2)))
            i += 1
            continue

        if (
            _TABLE_ROW_RE.match(stripped)
            and i + 1 < len(lines)
            and _TABLE_SEP_RE.match(lines[i + 1].strip())
        ):
            flush_paragraph()
            rows = [_split_table_row(stripped)]
            i += 2
            while i < len(lines) and _TABLE_ROW_RE.match(lines[i].strip()):
                rows.append(_split_table_row(lines[i].strip()))
                i += 1
            blocks.append(_table(rows))
            continue

        if stripped in ("---", "***", "___"):
            flush_paragraph()
            blocks.append(_divider())
            i += 1
            continue

        todo_match = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)$", stripped)
        if todo_match:
            flush_paragraph()
            blocks.append(_todo(todo_match.group(2), todo_match.group(1).lower() == "x"))
            i += 1
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet_match:
            flush_paragraph()
            blocks.append(_bulleted(bullet_match.group(1)))
            i += 1
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered_match:
            flush_paragraph()
            blocks.append(_numbered(numbered_match.group(1)))
            i += 1
            continue

        quote_match = re.match(r"^>\s?(.*)$", stripped)
        if quote_match:
            flush_paragraph()
            blocks.append(_quote(quote_match.group(1)))
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        paragraph_buffer.append(stripped)
        i += 1

    flush_paragraph()
    return blocks


def _rich_text_to_markdown(rich_text: list[dict]) -> str:
    parts = []
    for rt in rich_text:
        content = rt.get("plain_text", rt.get("text", {}).get("content", ""))
        annotations = rt.get("annotations", {})
        if annotations.get("code"):
            content = f"`{content}`"
        elif annotations.get("bold") and annotations.get("italic"):
            content = f"***{content}***"
        elif annotations.get("bold"):
            content = f"**{content}**"
        elif annotations.get("italic"):
            content = f"*{content}*"
        parts.append(content)
    return "".join(parts)


def _block_to_markdown(block: dict) -> str | None:
    block_type = block.get("type")
    data = block.get(block_type, {})

    if block_type == "paragraph":
        return _rich_text_to_markdown(data.get("rich_text", []))
    if block_type in ("heading_1", "heading_2", "heading_3"):
        level = int(block_type[-1])
        return f"{'#' * level} {_rich_text_to_markdown(data.get('rich_text', []))}"
    if block_type == "bulleted_list_item":
        return f"- {_rich_text_to_markdown(data.get('rich_text', []))}"
    if block_type == "numbered_list_item":
        return f"1. {_rich_text_to_markdown(data.get('rich_text', []))}"
    if block_type == "to_do":
        mark = "x" if data.get("checked") else " "
        return f"- [{mark}] {_rich_text_to_markdown(data.get('rich_text', []))}"
    if block_type == "quote":
        return f"> {_rich_text_to_markdown(data.get('rich_text', []))}"
    if block_type == "divider":
        return "---"
    if block_type == "code":
        language = data.get("language", "")
        code_text = _rich_text_to_markdown(data.get("rich_text", []))
        return f"```{language}\n{code_text}\n```"
    if block_type == "table":
        rows = data.get("children", [])
        lines = []
        for idx, row in enumerate(rows):
            cells = row.get("table_row", {}).get("cells", [])
            lines.append("| " + " | ".join(_rich_text_to_markdown(cell) for cell in cells) + " |")
            if idx == 0:
                lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
        return "\n".join(lines)
    if block_type == "toggle":
        summary = _rich_text_to_markdown(data.get("rich_text", []))
        inner = blocks_to_markdown(data.get("children", []))
        return f"<details>\n<summary>{summary}</summary>\n\n{inner}\n\n</details>"
    return None


def _indent(text: str, spaces: int = 2) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.split("\n"))


_LIST_TYPES = {"bulleted_list_item", "numbered_list_item", "to_do"}


def blocks_to_markdown(blocks: list[dict]) -> str:
    chunks = []
    numbered_count = 0
    prev_type = None

    for block in blocks:
        block_type = block.get("type")
        if block_type == "numbered_list_item":
            numbered_count = numbered_count + 1 if prev_type == "numbered_list_item" else 1
            data = block.get(block_type, {})
            md = f"{numbered_count}. {_rich_text_to_markdown(data.get('rich_text', []))}"
        else:
            md = _block_to_markdown(block)

        if md is None:
            prev_type = block_type
            continue

        if block_type not in ("table", "toggle"):
            nested = block.get(block_type, {}).get("children")
            if nested:
                md = md + "\n" + _indent(blocks_to_markdown(nested))

        separator = "\n" if block_type in _LIST_TYPES and prev_type in _LIST_TYPES else "\n\n"
        if chunks:
            chunks.append(separator)
        chunks.append(md)
        prev_type = block_type

    return "".join(chunks)


async def _list_children(block_id: str) -> list[dict]:
    children: list[dict] = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        result = await get(f"/blocks/{block_id}/children", params=params)
        children.extend(result.get("results", []))
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
    return children


async def _expand_children(blocks: list[dict]) -> list[dict]:
    for block in blocks:
        if block.get("has_children"):
            nested = await _list_children(block["id"])
            block.setdefault(block["type"], {})["children"] = await _expand_children(nested)
    return blocks


async def get_page_body(page_id: str) -> dict:
    children = await _expand_children(await _list_children(page_id))
    return {"page_id": page_id, "markdown": blocks_to_markdown(children)}


async def update_page_body(page_id: str, markdown: str) -> dict:
    # Build and validate the new blocks locally before touching the page, then append
    # them ahead of deleting the old ones. This avoids a moment where the page is empty
    # (flicker) and means a failed append leaves the original content intact instead of
    # a half-cleared page.
    new_blocks = markdown_to_blocks(markdown)
    existing = await _list_children(page_id)

    for i in range(0, len(new_blocks), 100):
        chunk = new_blocks[i : i + 100]
        await patch(f"/blocks/{page_id}/children", {"children": chunk})

    for block in existing:
        await delete(f"/blocks/{block['id']}")

    return {"page_id": page_id, "block_count": len(new_blocks)}
