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

    payload: dict[str, Any] = {
        "title": command.title,
        "url": command.url,
        "streamType": "hls",
        "enterPip": command.enter_pip,
    }
    if command.duration_seconds is not None:
        payload["durationSeconds"] = command.duration_seconds

    await asyncio.to_thread(
        _post_json,
        host,
        port,
        "/show",
        payload,
        token,
    )


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


def _error_message(body: str) -> str | None:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    value = parsed.get("error")
    return str(value) if value else None
