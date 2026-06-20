from ..client import get, patch


async def get_page(page_id: str) -> dict:
    return await get(f"/pages/{page_id}")


async def update_page_properties(page_id: str, properties: dict) -> dict:
    return await patch(f"/pages/{page_id}", {"properties": properties})
