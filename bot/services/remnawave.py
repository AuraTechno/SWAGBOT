import logging
from datetime import datetime, timezone, timedelta
import httpx
from bot.config import config

logger = logging.getLogger(__name__)

_headers: dict | None = None


def _get_headers() -> dict:
    global _headers
    if _headers is None:
        _headers = {
            "Authorization": f"Bearer {config.REMNAWAVE_TOKEN}",
            "Content-Type": "application/json",
        }
    return _headers


async def _api_request(method: str, path: str, json_data: dict | None = None) -> dict | None:
    url = f"{config.REMNAWAVE_BASE_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=_get_headers(),
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Remnawave API error [{method} {path}]: {e}")
        return None


async def create_user(
    username: str,
    expire_days: int,
    data_limit_gb: int = 0,
    node_uuid: str | None = None,
    email: str | None = None,
) -> dict | None:
    payload = {
        "username": username,
        "expireAt": (datetime.now(timezone.utc) + timedelta(days=expire_days)).isoformat(),
        "dataLimit": data_limit_gb * 1024**3 if data_limit_gb > 0 else 0,
        "nodeUuid": node_uuid or config.REMNAWAVE_NODE_UUID,
    }
    if email:
        payload["email"] = email
    return await _api_request("POST", "/api/users/create", payload)


async def delete_user(uuid: str) -> bool:
    result = await _api_request("DELETE", f"/api/users/{uuid}")
    return result is not None


async def extend_user(uuid: str, additional_days: int) -> bool:
    result = await _api_request("PUT", f"/api/users/{uuid}/extend", {
        "days": additional_days,
    })
    return result is not None


async def get_user(uuid: str) -> dict | None:
    return await _api_request("GET", f"/api/users/{uuid}")


async def get_all_users() -> list[dict]:
    result = await _api_request("GET", "/api/users")
    if result:
        return result.get("users", [])
    return []


async def get_server_stats() -> dict:
    result = await _api_request("GET", "/api/users")
    if result:
        users = result.get("users", [])
        total = len(users)
        active = sum(1 for u in users if u.get("isActive", False))
        return {"total": total, "active": active}
    return {"total": 0, "active": 0}


async def disable_user(uuid: str) -> bool:
    result = await _api_request("PUT", f"/api/users/{uuid}/disable")
    return result is not None


async def enable_user(uuid: str) -> bool:
    result = await _api_request("PUT", f"/api/users/{uuid}/enable")
    return result is not None


async def get_user_subscription_link(uuid: str) -> str | None:
    result = await _api_request("GET", f"/api/users/{uuid}")
    if result:
        return result.get("subscriptionUrl")
    return None
