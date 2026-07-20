from ..client import get, post, patch, NotionAPIError
from ..config import TASK_LIST_DB_ID, TASK_TEMPLATE_ID, TASK_STATUSES


def _page_title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(p["plain_text"] for p in prop.get("title", []))
    return ""


async def _resolve_name(title_parts: list[dict], page_title_cache: dict[str, str | None]) -> dict:
    segments = []
    unresolved_page_id = None
    for part in title_parts:
        mention = part.get("mention") if part.get("type") == "mention" else None
        page_id = mention.get("page", {}).get("id") if mention and mention.get("type") == "page" else None
        if page_id is None:
            segments.append(part["plain_text"])
            continue

        if page_id not in page_title_cache:
            try:
                page_title_cache[page_id] = _page_title(await get(f"/pages/{page_id}"))
            except NotionAPIError:
                page_title_cache[page_id] = None

        resolved = page_title_cache[page_id]
        if resolved is None:
            unresolved_page_id = page_id
            segments.append(part["plain_text"])
        else:
            segments.append(resolved)

    name = "".join(segments)
    return {"name": name, "mentioned_page_id": unresolved_page_id} if unresolved_page_id else {"name": name}


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
    page_title_cache: dict[str, str | None] = {}
    for page in result.get("results", []):
        props = page["properties"]
        title_parts = (props.get("Name") or {}).get("title", [])
        select = (props.get("Status") or {}).get("select") or {}
        name_info = await _resolve_name(title_parts, page_title_cache)
        task = {
            "id": page["id"],
            "url": page["url"],
            "name": name_info["name"],
            "status": select.get("name"),
        }
        if "mentioned_page_id" in name_info:
            task["unresolved_mention"] = True
            task["mentioned_page_id"] = name_info["mentioned_page_id"]
        tasks.append(task)
    return tasks


async def update_task_status(task_id: str, status: str) -> dict:
    if status not in TASK_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {TASK_STATUSES}")

    page = await patch(f"/pages/{task_id}", {
        "properties": {"Status": {"select": {"name": status}}}
    })
    return {"id": page["id"], "status": status}
