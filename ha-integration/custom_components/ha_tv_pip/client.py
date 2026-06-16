"""Local HTTP client for HA TV PiP receivers."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ReceiverClientError(Exception):
    """Raised when the receiver rejects or fails a local request."""


@dataclass(frozen=True)
class PairingStartResult:
    """Receiver response after starting pairing."""

    pairing_state: str
    expires_in_seconds: int


@dataclass(frozen=True)
class PairingConfirmResult:
    """Receiver response after confirming pairing."""

    token: str
    client_id: str
    client_name: str


@dataclass(frozen=True)
class ShowCameraCommand:
    """Command payload sent to the receiver to show a camera stream."""

    title: str
    url: str
    duration_seconds: int | None
    enter_pip: bool
    stream_type: str = "hls"
    preview_url: str | None = None


def show_camera_payload(command: ShowCameraCommand) -> dict[str, Any]:
    """Convert a show-camera command into the receiver wire payload."""

    payload: dict[str, Any] = {
        "title": command.title,
        "url": command.url,
        "streamType": command.stream_type,
        "enterPip": command.enter_pip,
    }
    if command.duration_seconds is not None:
        payload["durationSeconds"] = command.duration_seconds
    if command.preview_url is not None:
        payload["previewUrl"] = command.preview_url
    return payload


@dataclass(frozen=True)
class ReceiverStatus:
    """Receiver status returned by the local HTTP API."""

    app: str
    version: str
    device_id: str
    device_name: str
    api_version: int | None
    control_running: bool
    playback_state: str
    display_mode: str
    pairing_state: str | None
    launcher_visible: bool | None
    remote_status: str | None
    last_request: dict[str, Any] | None
    error: str | None
    raw: dict[str, Any]


async def async_start_pairing(
    host: str,
    port: int,
    *,
    client_id: str,
    client_name: str,
) -> PairingStartResult:
    """Ask the receiver to show a pairing code on the TV."""

    payload = {
        "clientId": client_id,
        "clientName": client_name,
    }
    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/pair/start",
        payload,
    )
    return PairingStartResult(
        pairing_state=str(response.get("pairingState", "pending")),
        expires_in_seconds=int(response.get("expiresInSeconds", 300)),
    )


async def async_confirm_pairing(
    host: str,
    port: int,
    *,
    client_id: str,
    client_name: str,
    code: str,
) -> PairingConfirmResult:
    """Confirm the TV-visible pairing code and receive a local auth token."""

    payload = {
        "clientId": client_id,
        "clientName": client_name,
        "code": code,
    }
    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/pair/confirm",
        payload,
    )

    token = str(response.get("token", "")).strip()
    if not token:
        raise ReceiverClientError("missing_token")

    return PairingConfirmResult(
        token=token,
        client_id=str(response.get("clientId", client_id)),
        client_name=str(response.get("clientName", client_name)),
    )


async def async_show_camera(
    host: str,
    port: int,
    *,
    token: str,
    command: ShowCameraCommand,
) -> None:
    """Ask the paired receiver to display a camera stream."""

    await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/show",
        show_camera_payload(command),
        token,
    )


async def async_get_receiver_status(host: str, port: int) -> ReceiverStatus:
    """Fetch receiver status from the local API."""

    response = await asyncio.to_thread(_get_json, host, port, "/status")
    pairing = response.get("pairing")
    management = response.get("management")
    remote = response.get("remote")
    last_request = response.get("lastRequest")
    return ReceiverStatus(
        app=str(response.get("app", "HA TV PiP Receiver")),
        version=str(response.get("version", "")),
        device_id=str(response.get("deviceId", "")),
        device_name=str(response.get("deviceName", "")),
        api_version=_optional_int(response.get("apiVersion")),
        control_running=bool(response.get("controlRunning", False)),
        playback_state=str(response.get("playbackState", "unknown")),
        display_mode=str(response.get("displayMode", "unknown")),
        pairing_state=str(pairing.get("state")) if isinstance(pairing, dict) else None,
        launcher_visible=(
            bool(management["launcherVisible"])
            if isinstance(management, dict) and "launcherVisible" in management
            else None
        ),
        remote_status=(
            str(remote["status"])
            if isinstance(remote, dict) and remote.get("status")
            else None
        ),
        last_request=last_request if isinstance(last_request, dict) else None,
        error=str(response["error"]) if response.get("error") else None,
        raw=response,
    )


async def async_close_receiver(host: str, port: int, *, token: str) -> bool:
    """Ask the paired receiver to close the active display."""

    response = await asyncio.to_thread(_post_json, host, port, "/close", {}, token)
    return bool(response.get("accepted", False))


async def async_open_receiver(host: str, port: int, *, token: str) -> bool:
    """Ask the paired receiver to open its management screen."""

    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/management/open",
        {},
        token,
    )
    return bool(response.get("accepted", False))


async def async_set_launcher_visible(
    host: str,
    port: int,
    *,
    token: str,
    visible: bool,
) -> bool:
    """Show or hide the receiver launcher icon."""

    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/management/launcher",
        {"visible": visible},
        token,
    )
    return bool(response.get("launcherVisible", visible))


async def async_set_remote_configuration(
    host: str,
    port: int,
    *,
    token: str,
    home_assistant_url: str,
    access_token: str,
) -> bool:
    """Store remote receiver connection settings on the paired receiver."""

    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/management/remote",
        {
            "homeAssistantUrl": home_assistant_url,
            "accessToken": access_token,
        },
        token,
    )
    return bool(response.get("accepted", False))


async def async_clear_remote_configuration(
    host: str,
    port: int,
    *,
    token: str,
) -> bool:
    """Clear remote receiver connection settings on the paired receiver."""

    response = await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/management/remote",
        {"clear": True},
        token,
    )
    return bool(response.get("accepted", False))


def _post_json(
    host: str,
    port: int,
    path: str,
    payload: dict[str, Any],
    token: str | None = None,
) -> dict[str, Any]:
    url = f"http://{host}:{port}{path}"
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310
            body = response.read().decode()
    except HTTPError as error:
        body = error.read().decode()
        message = _error_message(body) or f"http_{error.code}"
        raise ReceiverClientError(message) from error
    except (TimeoutError, URLError) as error:
        raise ReceiverClientError("cannot_connect") from error

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as error:
        raise ReceiverClientError("invalid_response") from error

    if not isinstance(parsed, dict):
        raise ReceiverClientError("invalid_response")

    return parsed


def _get_json(host: str, port: int, path: str) -> dict[str, Any]:
    url = f"http://{host}:{port}{path}"
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310
            body = response.read().decode()
    except HTTPError as error:
        body = error.read().decode()
        message = _error_message(body) or f"http_{error.code}"
        raise ReceiverClientError(message) from error
    except (TimeoutError, URLError) as error:
        raise ReceiverClientError("cannot_connect") from error

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as error:
        raise ReceiverClientError("invalid_response") from error

    if not isinstance(parsed, dict):
        raise ReceiverClientError("invalid_response")

    return parsed


def _error_message(body: str) -> str | None:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    value = parsed.get("error")
    return str(value) if value else None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
