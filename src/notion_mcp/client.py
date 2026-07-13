import httpx
from .config import NOTION_API_KEY, NOTION_API_BASE, NOTION_VERSION


class NotionAPIError(Exception):
    """Raised with Notion's actual error body instead of httpx's generic status message."""

    def __init__(self, status_code: int, body: dict | str):
        self.status_code = status_code
        self.body = body
        message = body.get("message") if isinstance(body, dict) else body
        super().__init__(f"Notion API error {status_code}: {message}")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_error:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        raise NotionAPIError(response.status_code, body)


async def get(path: str, **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTION_API_BASE}{path}", headers=_headers(), **kwargs)
        _raise_for_status(response)
        return response.json()


async def post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{NOTION_API_BASE}{path}", headers=_headers(), json=body)
        _raise_for_status(response)
        return response.json()


async def patch(path: str, body: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.patch(f"{NOTION_API_BASE}{path}", headers=_headers(), json=body)
        _raise_for_status(response)
        return response.json()


async def delete(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{NOTION_API_BASE}{path}", headers=_headers())
        _raise_for_status(response)
        return response.json()
