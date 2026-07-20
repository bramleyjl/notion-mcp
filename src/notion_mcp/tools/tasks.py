from ..client import get, post, patch
from ..config import TASK_LIST_DB_ID, TASK_TEMPLATE_ID, TASK_STATUSES


async def create_task(name: str, status: str = "To Do", url: str | None = None) -> dict:
    if status not in TASK_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {TASK_STATUSES}")

    page = await post("/pages", {
        "parent": {"database_id": TASK_LIST_DB_ID},
        "template_id": TASK_TEMPLATE_ID,
        "properties": {
            "Name": {"title": [{"text": {"content": name}}]},
            "Status": {"select": {"name": status}},
            **({"userDefined:URL": {"url": url}} if url else {}),
        },
    })
    return {"id": page["id"], "url": page["url"], "name": name, "status": status}


async def get_tasks(status: str | None = None) -> list[dict]:
    body: dict = {"page_size": 100}
    if status:
        body["filter"] = {"property": "Status", "select": {"equals": status}}

    result = await post("/databases/" + TASK_LIST_DB_ID + "/query", body)
    tasks = []
    for page in result.get("results", []):
        props = page["properties"]
        title_parts = props.get("Name", {}).get("title", [])
        tasks.append({
            "id": page["id"],
            "url": page["url"],
            "name": "".join(p["plain_text"] for p in title_parts),
            "status": props.get("Status", {}).get("select", {}).get("name"),
        })
    return tasks


async def update_task_status(task_id: str, status: str) -> dict:
    if status not in TASK_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {TASK_STATUSES}")

    page = await patch(f"/pages/{task_id}", {
        "properties": {"Status": {"select": {"name": status}}}
    })
    return {"id": page["id"], "status": status}
