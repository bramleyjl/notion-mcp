# notion-mcp

Personal Notion MCP server with domain-specific tools for task management and workspace integration. Wraps the Notion REST API with tools that encode workspace-specific structure (database IDs, templates, status values) so callers don't need to know the details.

## Tools

| Tool | Description |
|------|-------------|
| `notion_create_task` | Create a task in the Task List kanban board |
| `notion_get_tasks` | Query tasks, optionally filtered by status |
| `notion_update_task_status` | Move a task to a new kanban column |

## Setup

### Prerequisites

- Python 3.12+
- A Notion integration with access to the target workspace

### Installation

```bash
git clone git@github.com:bramleyjl/notion-mcp.git ~/Projects/mcps/notion-mcp
cd ~/Projects/mcps/notion-mcp
pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Edit .env and set NOTION_API_KEY to your Notion integration token
```

Get a token at [notion.so/my-integrations](https://www.notion.so/my-integrations) — create an internal integration and share your target databases with it.

### Running

```bash
notion-mcp
```

Or as a background service — see `deploy/` for systemd unit examples.

## MCP Config

Add to `~/.claude/settings.json` under `mcpServers`:

```json
"notion-mcp": {
  "type": "stdio",
  "command": "notion-mcp",
  "env": {
    "NOTION_API_KEY": "your_token_here"
  }
}
```
