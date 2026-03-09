from datetime import datetime
from typing import Optional
import httpx

from .config import settings


class APIClient:
    def __init__(self):
        self._client = httpx.AsyncClient(base_url=settings.api_base_url, timeout=10.0)

    async def close(self):
        await self._client.aclose()

    async def get_family_by_chat(self, chat_id: int) -> dict | None:
        r = await self._client.get(f"/api/families/{chat_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def list_families(self) -> list[dict]:
        r = await self._client.get("/api/families")
        r.raise_for_status()
        return r.json()

    async def create_family(self, name: str, chat_id: int, timezone: str = "UTC") -> dict:
        r = await self._client.post("/api/families", json={"name": name, "chat_id": chat_id, "timezone": timezone})
        r.raise_for_status()
        return r.json()

    async def get_member_by_user(self, user_id: int, family_id: int) -> dict | None:
        r = await self._client.get("/api/members/by_user", params={"user_id": user_id, "family_id": family_id})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def create_member(self, family_id: int, user_id: int, username: Optional[str], display_name: str, role: str = "member") -> dict:
        r = await self._client.post("/api/members", json={
            "family_id": family_id,
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "role": role,
        })
        r.raise_for_status()
        return r.json()

    async def get_or_create_member(self, family_id: int, user_id: int, username: Optional[str], display_name: str, role: str = "member") -> dict:
        member = await self.get_member_by_user(user_id, family_id)
        if member:
            return member
        return await self.create_member(family_id, user_id, username, display_name, role)

    async def get_family_by_id(self, family_id: int) -> dict | None:
        r = await self._client.get(f"/api/families/by_id/{family_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def get_user_memberships(self, user_id: int) -> list[dict]:
        r = await self._client.get("/api/members", params={"user_id": user_id})
        r.raise_for_status()
        return r.json()

    async def list_members(self, family_id: int) -> list[dict]:
        r = await self._client.get("/api/members", params={"family_id": family_id})
        r.raise_for_status()
        return r.json()

    async def update_member_role(self, member_id: int, role: str) -> dict:
        r = await self._client.patch(f"/api/members/{member_id}", json={"role": role})
        r.raise_for_status()
        return r.json()

    async def create_chore(self, payload: dict) -> dict:
        r = await self._client.post("/api/chores", json=payload)
        r.raise_for_status()
        return r.json()

    async def list_chores(self, **filters) -> list[dict]:
        r = await self._client.get("/api/chores", params={k: v for k, v in filters.items() if v is not None})
        r.raise_for_status()
        return r.json()

    async def patch_chore(self, chore_id: int, payload: dict) -> dict:
        r = await self._client.patch(f"/api/chores/{chore_id}", json=payload)
        r.raise_for_status()
        return r.json()

    async def assign_chore(self, chore_id: int, mode: str, assigned_to: Optional[int] = None) -> dict:
        body = {"mode": mode}
        if assigned_to is not None:
            body["assigned_to"] = assigned_to
        r = await self._client.post(f"/api/chores/{chore_id}/assign", json=body)
        r.raise_for_status()
        return r.json()

    async def complete_chore(self, chore_id: int, user_id: int, photo_url: Optional[str] = None) -> dict:
        r = await self._client.post(f"/api/chores/{chore_id}/complete", json={"user_id": user_id, "photo_url": photo_url})
        r.raise_for_status()
        return r.json()

    async def get_history(self, family_id: int, from_dt: Optional[datetime] = None, to_dt: Optional[datetime] = None) -> list[dict]:
        params: dict = {"family_id": family_id}
        if from_dt:
            params["from_dt"] = from_dt.isoformat()
        if to_dt:
            params["to_dt"] = to_dt.isoformat()
        r = await self._client.get("/api/chores/history", params=params)
        r.raise_for_status()
        return r.json()


api = APIClient()
