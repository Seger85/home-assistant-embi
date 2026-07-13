from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout


class EmbyApiError(Exception):
    """Base exception for Emby API errors."""


class EmbyAuthError(EmbyApiError):
    """Authentication failed."""


@dataclass(slots=True)
class EmbyDeviceRecord:
    """A device record returned by the local Emby server."""

    id: str
    name: str
    app_name: str | None = None
    app_version: str | None = None
    last_user_name: str | None = None
    last_activity_date: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "EmbyDeviceRecord":
        return cls(
            id=str(data.get("Id", "")),
            name=str(data.get("Name") or data.get("ReportedDeviceName") or "Unknown"),
            app_name=data.get("AppName"),
            app_version=data.get("AppVersion"),
            last_user_name=data.get("LastUserName"),
            last_activity_date=data.get("DateLastActivity") or data.get("LastActivityDate"),
        )

    @property
    def player_key(self) -> str:
        """Return the exact key used by pyemby / Home Assistant unique_id."""
        return f"{self.id}.{self.app_name}" if self.app_name else self.id

    @property
    def label(self) -> str:
        details = [self.name]
        if self.app_name:
            details.append(self.app_name)
        if self.last_user_name:
            details.append(self.last_user_name)
        return " · ".join(details)

    def as_diagnostics(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "player_key": self.player_key,
            "name": self.name,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "last_user_name": self.last_user_name,
            "last_activity_date": self.last_activity_date,
        }


class EmbyApiClient:
    """Small asynchronous client for the local Emby REST API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        api_key: str,
        use_ssl: bool,
    ) -> None:
        self._session = session
        scheme = "https" if use_ssl else "http"
        self.base_url = f"{scheme}://{host}:{int(port)}"
        self._headers = {"X-Emby-Token": api_key, "Accept": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers,
                timeout=ClientTimeout(total=15),
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise EmbyAuthError("The Emby API key was rejected")
                response.raise_for_status()
                if response.status == 204:
                    return None
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type:
                    return await response.json()
                text = await response.text()
                return text or None
        except EmbyAuthError:
            raise
        except (ClientResponseError, ClientError, TimeoutError) as err:
            raise EmbyApiError(str(err)) from err

    async def async_validate(self) -> dict[str, Any]:
        data = await self._request("GET", "/System/Info")
        if not isinstance(data, dict):
            raise EmbyApiError("Unexpected response from the Emby server")
        return data

    async def async_get_devices(self) -> list[EmbyDeviceRecord]:
        data = await self._request("GET", "/Devices")
        if isinstance(data, dict):
            raw_items = data.get("Items", [])
            items = raw_items if isinstance(raw_items, list) else []
        elif isinstance(data, list):
            items = data
        else:
            items = []
        records = [EmbyDeviceRecord.from_api(item) for item in items if item.get("Id")]
        return sorted(records, key=lambda item: item.label.casefold())

    async def async_delete_device(self, device_id: str) -> None:
        """Delete one explicitly selected device from the Emby server history."""
        await self._request("DELETE", "/Devices", params={"Id": device_id})
