from ..client import get, NotionAPIError


def page_title(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(p["plain_text"] for p in prop.get("title", []))
    return ""


async def resolve_page_title(page_id: str, cache: dict[str, str | None]) -> str | None:
    """Resolve a mentioned page's live title, caching results (including failures) by page_id.

    Returns None if the page isn't resolvable (e.g. not shared with the integration),
    so callers can fall back to Notion's stale cached mention text instead.
    """
    if page_id not in cache:
        try:
            cache[page_id] = page_title(await get(f"/pages/{page_id}"))
        except NotionAPIError:
            cache[page_id] = None
    return cache[page_id]
