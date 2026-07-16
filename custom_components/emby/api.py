from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout


class EmbyApiError(Exception):
    """Base exception for Emby API errors."""


class EmbyAuthError(EmbyApiError):
    """Authentication failed."""


def _parse_emby_datetime(value: str | None) -> datetime | None:
    """Parse Emby ISO timestamps, including seven-digit fractional seconds."""
    if not value:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    match = re.fullmatch(
        r"(?P<prefix>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
        r"(?:\.(?P<fraction>\d+))?"
        r"(?P<offset>[+-]\d{2}:\d{2})?",
        normalized,
    )
    if match:
        fraction = match.group("fraction")
        offset = match.group("offset") or "+00:00"
        normalized = match.group("prefix")
        if fraction:
            normalized = f"{normalized}.{fraction[:6]}"
        normalized = f"{normalized}{offset}"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_bool(*values: Any) -> bool | None:
    """Return the first explicit boolean-like value without guessing missing metadata."""
    for value in values:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"true", "yes", "1"}:
                return True
            if normalized in {"false", "no", "0"}:
                return False
    return None


def _user_names(data: dict[str, Any]) -> tuple[str, ...]:
    """Extract explicitly named users from the device record."""
    names: set[str] = set()
    for key in ("LastUserName", "UserName"):
        value = data.get(key)
        if value and str(value).strip():
            names.add(str(value).strip())

    for key in ("UserNames", "Users"):
        raw = data.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            value = (
                item.get("Name") or item.get("UserName")
                if isinstance(item, dict)
                else item
            )
            if value and str(value).strip():
                names.add(str(value).strip())
    return tuple(sorted(names, key=str.casefold))


def _capabilities(data: dict[str, Any]) -> tuple[str, ...]:
    """Normalize explicit client capabilities without using product-name guesses."""
    values: set[str] = set()
    raw = data.get("Capabilities") or data.get("ClientCapabilities")
    if isinstance(raw, list):
        values.update(str(item).strip().casefold() for item in raw if str(item).strip())
    elif isinstance(raw, dict):
        values.update(
            str(key).strip().casefold()
            for key, enabled in raw.items()
            if enabled and str(key).strip()
        )
    elif isinstance(raw, str):
        values.update(part.strip().casefold() for part in raw.split(",") if part.strip())
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class EmbyDeviceRecord:
    """A device-history record returned by the local Emby server."""

    record_id: str
    reported_device_id: str
    name: str
    app_name: str | None = None
    app_version: str | None = None
    last_user_name: str | None = None
    last_activity_date: str | None = None
    user_names: tuple[str, ...] = ()
    client_type: str | None = None
    capabilities: tuple[str, ...] = ()
    supports_playback: bool | None = None
    api_only: bool | None = None
    playback_observed: bool = False

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> EmbyDeviceRecord:
        """Create a normalized record from Emby's /Devices response.

        Emby exposes two different identifiers:
        - Id: the server-side device-history record used by DELETE /Devices
        - ReportedDeviceId: the client identity used by pyemby and HA unique IDs
        """
        record_id = str(data.get("Id") or "")
        reported_device_id = str(data.get("ReportedDeviceId") or record_id)
        capabilities = _capabilities(data)
        supports_playback = _optional_bool(
            data.get("SupportsPlayback"),
            data.get("SupportsMediaControl"),
            data.get("CanPlayMedia"),
        )
        if supports_playback is None and capabilities:
            playback_capabilities = {
                "playback",
                "play_media",
                "media_control",
                "remote_control",
                "supports_playback",
            }
            if playback_capabilities & set(capabilities):
                supports_playback = True

        api_only = _optional_bool(data.get("IsApiOnly"), data.get("ApiOnly"))
        client_type = data.get("ClientType") or data.get("ConnectionType")
        playback_observed = bool(
            data.get("LastPlaybackDate")
            or data.get("NowPlayingItem")
            or data.get("HasPlaybackSession")
        )
        users = _user_names(data)
        last_user = data.get("LastUserName") or data.get("UserName")
        return cls(
            record_id=record_id,
            reported_device_id=reported_device_id,
            name=str(data.get("Name") or data.get("ReportedDeviceName") or "Unknown"),
            app_name=data.get("AppName"),
            app_version=data.get("AppVersion"),
            last_user_name=str(last_user).strip() if last_user else None,
            last_activity_date=data.get("DateLastActivity") or data.get("LastActivityDate"),
            user_names=users,
            client_type=str(client_type).strip() if client_type else None,
            capabilities=capabilities,
            supports_playback=supports_playback,
            api_only=api_only,
            playback_observed=playback_observed,
        )

    @property
    def player_key(self) -> str:
        """Return the key used by pyemby and existing HA entity unique IDs."""
        if self.app_name:
            return f"{self.reported_device_id}.{self.app_name}"
        return self.reported_device_id

    @property
    def last_activity_datetime(self) -> datetime | None:
        """Return the normalized UTC timestamp used by age-based cleanup."""
        return _parse_emby_datetime(self.last_activity_date)

    @property
    def label(self) -> str:
        """Return a user-facing selector label without exposing an internal identifier."""
        details = [self.name]
        if self.app_name:
            details.append(self.app_name)
        if self.last_user_name:
            details.append(self.last_user_name)
        return " · ".join(details)

    @property
    def short_record_id(self) -> str:
        """Return a compact identifier for diagnostics only."""
        if len(self.record_id) <= 8:
            return self.record_id
        return f"{self.record_id[:4]}…{self.record_id[-4:]}"

    @property
    def activity_label(self) -> str | None:
        """Return a compact, stable display value for the last activity timestamp."""
        parsed = self.last_activity_datetime
        if parsed is not None:
            return parsed.strftime("%Y-%m-%d %H:%M UTC")
        if self.last_activity_date:
            return str(self.last_activity_date).strip()
        return None

    @property
    def server_cleanup_label(self) -> str:
        """Return a friendly label for one exact server-history record."""
        details = [self.name]
        app = self.app_name or "Unknown app"
        if self.app_version:
            app = f"{app} {self.app_version}"
        details.append(app)
        if self.last_user_name:
            details.append(self.last_user_name)
        if self.activity_label:
            details.append(self.activity_label)
        return " · ".join(details)


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
        except (ClientError, TimeoutError) as err:
            raise EmbyApiError(str(err)) from err

    async def async_validate(self) -> dict[str, Any]:
        """Validate connectivity and credentials."""
        data = await self._request("GET", "/System/Info")
        if not isinstance(data, dict):
            raise EmbyApiError("Unexpected response from the Emby server")
        return data

    async def async_get_devices(self) -> list[EmbyDeviceRecord]:
        """Return normalized device-history records."""
        data = await self._request("GET", "/Devices")
        if isinstance(data, dict):
            raw_items = data.get("Items", [])
            items = raw_items if isinstance(raw_items, list) else []
        elif isinstance(data, list):
            items = data
        else:
            items = []

        records = [
            EmbyDeviceRecord.from_api(item)
            for item in items
            if isinstance(item, dict) and item.get("Id")
        ]
        return sorted(records, key=lambda item: item.label.casefold())

    async def async_delete_device(self, record_id: str) -> None:
        """Delete one explicitly selected device-history record."""
        await self._request("DELETE", "/Devices", params={"Id": record_id})
