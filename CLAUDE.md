# notion-mcp — AI Context

## Architecture

- `client.py` — thin wrappers (`get`/`post`/`patch`/`delete`) around `httpx`, shared auth headers. All Notion API calls go through these.
- `tools/*.py` — plain async functions doing the actual work (no MCP decorators here), one file per domain (`tasks.py`, `pages.py`, `blocks.py`).
- `server.py` — registers each `tools/` function as an `@mcp.tool()`-decorated wrapper with a docstring; this is the only place that imports `FastMCP`.

Keep new tools following this three-layer split: client → tools function → server registration.

## Notion API gotchas

- No "replace all children" endpoint exists. `notion_update_page_body` does a full replace by building+validating new blocks locally, `PATCH`-appending them (chunked at 100 per request — Notion's per-request block limit), and only then `DELETE`-ing the page's prior blocks. Append-before-delete is deliberate: it avoids a moment where the page reads empty, and a failed append leaves the original content intact instead of a half-cleared page. This is not a true block-level diff — it's a full rewrite each call, which is fine given the only caller (mtg-agent) always rewrites the whole doc anyway.
- Every `rich_text` segment's `text.content` is capped at 2000 chars by the Notion API. `_text_chunks()` in `tools/blocks.py` splits any run of text (including table cells) into multiple rich_text segments rather than sending one oversized one — a single markdown table cell over 2000 chars used to 400 the whole write.
- Block children listing (`GET /blocks/{id}/children`) paginates like databases — must follow `has_more`/`next_cursor`. Table blocks are a special case: their rows (`table_row` blocks) are *children* of the table block, not top-level page children, so `get_page_body` has to do a second `_list_children` call per table block to read rows back.
- No markdown-conversion library is used; `tools/blocks.py` has a small hand-rolled markdown↔block converter. It intentionally supports only what the working-notes use case needs: headings (1-3), paragraphs, bulleted/numbered lists, to-dos, quotes, code fences, dividers, GFM-style tables, and inline bold/italic/code. Extend it rather than pulling in a dependency unless requirements grow significantly.
- `client.py` raises `NotionAPIError` (carries the actual Notion error body/message) instead of letting httpx's generic `raise_for_status()` message through — callers on the MCP client side were previously only seeing an opaque "unhandled errors in a TaskGroup" with no diagnosable detail.

## Consumers

- `mtg-agent` calls this server over HTTP for all Notion interactions (auth lives only here). It added `clients/notion_mcp.py` + `tools/decks.py` (`get_deck_working_notes` / `update_deck_working_notes`) on top of `notion_get_page_body` / `notion_update_page_body` for a per-deck working-notes doc mirrored into MongoDB.
