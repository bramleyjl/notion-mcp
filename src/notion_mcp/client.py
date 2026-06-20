import httpx
from .config import NOTION_API_KEY, NOTION_API_BASE, NOTION_VERSION


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def get(path: str, **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTION_API_BASE}{path}", headers=_headers(), **kwargs)
        response.raise_for_status()
        return response.json()


async def post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{NOTION_API_BASE}{path}", headers=_headers(), json=body)
        response.raise_for_status()
        return response.json()


async def patch(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"{NOTION_API_BASE}{path}", headers=_headers(), json=body)
        response.raise_for_status()
        return response.json()
