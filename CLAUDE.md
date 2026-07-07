# notion-mcp — AI Context

## Architecture

- `client.py` — thin wrappers (`get`/`post`/`patch`/`delete`) around `httpx`, shared auth headers. All Notion API calls go through these.
- `tools/*.py` — plain async functions doing the actual work (no MCP decorators here), one file per domain (`tasks.py`, `pages.py`, `blocks.py`).
- `server.py` — registers each `tools/` function as an `@mcp.tool()`-decorated wrapper with a docstring; this is the only place that imports `FastMCP`.

Keep new tools following this three-layer split: client → tools function → server registration.

## Notion API gotchas

- No "replace all children" endpoint exists. `notion_update_page_body` does a full replace by listing existing block children, `DELETE`-ing each one individually, then `PATCH`-appending new blocks (chunked at 100 per request — Notion's per-request block limit).
- Block children listing (`GET /blocks/{id}/children`) paginates like databases — must follow `has_more`/`next_cursor`.
- No markdown-conversion library is used; `tools/blocks.py` has a small hand-rolled markdown↔block converter. It intentionally supports only what the working-notes use case needs: headings (1-3), paragraphs, bulleted/numbered lists, to-dos, quotes, code fences, dividers, and inline bold/italic/code. Extend it rather than pulling in a dependency unless requirements grow significantly.

## Consumers

- `mtg-agent` calls this server over HTTP for all Notion interactions (auth lives only here). It added `clients/notion_mcp.py` + `tools/decks.py` (`get_deck_working_notes` / `update_deck_working_notes`) on top of `notion_get_page_body` / `notion_update_page_body` for a per-deck working-notes doc mirrored into MongoDB.
