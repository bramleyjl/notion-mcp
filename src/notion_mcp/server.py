from mcp.server.fastmcp import FastMCP
from .tools.tasks import create_task, get_tasks, update_task_status

mcp = FastMCP("notion-mcp")


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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
