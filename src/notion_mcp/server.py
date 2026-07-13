import os

from mcp.server.fastmcp import FastMCP
from .tools.pages import get_page, update_page_properties
from .tools.tasks import create_task, get_tasks, update_task_status
from .tools.blocks import get_page_body, update_page_body

mcp = FastMCP(
    "notion-mcp",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8766")),
)


@mcp.tool()
async def notion_create_task(name: str, status: str = "To Do", url: str | None = None) -> dict:
    """Create a task in the Notion Task List kanban board."""
    return await create_task(name, status, url)


@mcp.tool()
async def notion_get_tasks(status: str | None = None) -> list:
    """Get tasks from the Notion Task List. Optionally filter by status."""
    return await get_tasks(status)


@mcp.tool()
async def notion_update_task_status(task_id: str, status: str) -> dict:
    """Move a Notion task to a new kanban status."""
    return await update_task_status(task_id, status)


@mcp.tool()
async def notion_get_page(page_id: str) -> dict:
    """Get a Notion page's properties and metadata by ID."""
    return await get_page(page_id)


@mcp.tool()
async def notion_update_page_properties(page_id: str, properties: dict) -> dict:
    """
    Update properties on a Notion page. `properties` must use the Notion API property format.

    Examples:
      Title field:    {"Name": {"title": [{"text": {"content": "value"}}]}}
      Rich text:      {"Summary": {"rich_text": [{"text": {"content": "value"}}]}}
      Select:         {"Status": {"select": {"name": "Active"}}}
      URL:            {"Link": {"url": "https://..."}}
      Checkbox:       {"Done": {"checkbox": true}}
    """
    return await update_page_properties(page_id, properties)


@mcp.tool()
async def notion_get_page_body(page_id: str) -> dict:
    """Get a Notion page's body content (blocks below the properties), converted to markdown."""
    return await get_page_body(page_id)


@mcp.tool()
async def notion_update_page_body(page_id: str, markdown: str) -> dict:
    """
    Replace a Notion page's body content with the given markdown.

    This performs a full replace: blocks parsed from `markdown` are appended first,
    then the page's prior blocks are deleted (append-before-delete, so a failure never
    leaves the page emptier than before). Supports headings (#, ##, ###), paragraphs,
    bulleted/numbered lists, to-do items (- [ ] / - [x]), blockquotes (>), code fences
    (```), dividers (---), GFM-style tables (| ... | header + | --- | separator rows),
    and inline **bold**/*italic*/`code`.
    """
    return await update_page_body(page_id, markdown)


def main():
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
