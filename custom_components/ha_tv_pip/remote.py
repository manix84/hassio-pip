"""Remote receiver transport for HA TV PiP.

Remote mode is still local-first in Home Assistant terms: the integration does
not depend on a vendor cloud. A receiver can optionally connect outbound to the
user's own Home Assistant WebSocket API, then HA can push commands down that
already-authenticated connection.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
from dataclasses import dataclass
from hmac import compare_digest
from typing import Any

from .client import (
    ReceiverStatus,
    ShowCameraCommand,
    receiver_status_from_payload,
    show_camera_payload,
)
from .const import CONF_DEVICE_ID, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_REMOTE_REGISTRY = "remote_registry"
DATA_REMOTE_API_REGISTERED = "remote_api_registered"
WS_TYPE_REGISTER = f"{DOMAIN}/receiver/register"
WS_TYPE_STATUS_RESPONSE = f"{DOMAIN}/receiver/status_response"
EVENT_RECEIVER_COMMAND = f"{DOMAIN}/receiver_command"


@dataclass
class RemoteReceiverConnection:
    """Active outbound receiver connection."""

    device_id: str
    connection: Any
    connection_id: str
    receiver_name: str | None = None


class RemoteReceiverRegistry:
    """Tracks receivers connected through Home Assistant's WebSocket API."""

    def __init__(self) -> None:
        self._connections: dict[str, RemoteReceiverConnection] = {}
        self._message_ids = itertools.count(1)
        self._pending_status: dict[int, tuple[str, asyncio.Future[ReceiverStatus]]] = {}

    def is_connected(self, device_id: str) -> bool:
        """Return whether a remote receiver is currently connected."""

        return device_id in self._connections

    def register(
        self,
        *,
        device_id: str,
        connection: Any,
        connection_id: str,
        receiver_name: str | None,
    ) -> None:
        """Register or replace an active remote receiver connection."""

        self._connections[device_id] = RemoteReceiverConnection(
            device_id=device_id,
            connection=connection,
            connection_id=connection_id,
            receiver_name=receiver_name,
        )
        _LOGGER.info("Remote HA TV PiP receiver connected: %s", device_id)

    def unregister(self, device_id: str, connection_id: str | None = None) -> None:
        """Remove an active remote receiver connection."""

        active = self._connections.get(device_id)
        if active is None:
            return
        if connection_id is not None and active.connection_id != connection_id:
            return
        self._connections.pop(device_id, None)
        _LOGGER.info("Remote HA TV PiP receiver disconnected: %s", device_id)

    async def async_send_show(
        self,
        *,
        device_id: str,
        command: ShowCameraCommand,
    ) -> bool:
        """Send a show command to a connected remote receiver."""

        remote = self._connections.get(device_id)
        if remote is None:
            return False

        remote.connection.send_message(
            {
                "id": next(self._message_ids),
                "type": "event",
                "event": {
                    "event_type": EVENT_RECEIVER_COMMAND,
                    "data": {
                        "command": "show",
                        "payload": show_camera_payload(command),
                    },
                },
            }
        )
        return True

    async def async_send_close(self, *, device_id: str) -> bool:
        """Send a close command to a connected remote receiver."""

        return self._send_command_event(
            device_id=device_id,
            data={"command": "close"},
        )

    async def async_get_status(
        self,
        *,
        device_id: str,
        timeout_seconds: float = 5.0,
    ) -> ReceiverStatus | None:
        """Request receiver status over the connected remote transport."""

        request_id = next(self._message_ids)
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ReceiverStatus] = loop.create_future()
        self._pending_status[request_id] = (device_id, future)
        accepted = self._send_command_event(
            device_id=device_id,
            data={
                "command": "status",
                "requestId": request_id,
            },
            message_id=request_id,
        )
        if not accepted:
            self._pending_status.pop(request_id, None)
            return None
        try:
            return await asyncio.wait_for(future, timeout=timeout_seconds)
        except TimeoutError:
            return None
        finally:
            self._pending_status.pop(request_id, None)

    def handle_status_response(
        self,
        *,
        device_id: str,
        request_id: int,
        status: dict[str, Any],
    ) -> bool:
        """Resolve a pending remote status request."""

        pending = self._pending_status.get(request_id)
        if pending is None:
            return False
        expected_device_id, future = pending
        if expected_device_id != device_id or future.done():
            return False
        future.set_result(receiver_status_from_payload(status))
        return True

    def _send_command_event(
        self,
        *,
        device_id: str,
        data: dict[str, Any],
        message_id: int | None = None,
    ) -> bool:
        remote = self._connections.get(device_id)
        if remote is None:
            return False

        remote.connection.send_message(
            {
                "id": message_id or next(self._message_ids),
                "type": "event",
                "event": {
                    "event_type": EVENT_RECEIVER_COMMAND,
                    "data": data,
                },
            }
        )
        return True


def remote_registry(hass: Any) -> RemoteReceiverRegistry:
    """Return the per-Home Assistant remote receiver registry."""

    data = hass.data.setdefault(DOMAIN, {})
    registry = data.get(DATA_REMOTE_REGISTRY)
    if isinstance(registry, RemoteReceiverRegistry):
        return registry
    registry = RemoteReceiverRegistry()
    data[DATA_REMOTE_REGISTRY] = registry
    return registry


async def async_setup_remote_api(hass: Any) -> None:
    """Register Home Assistant WebSocket commands used by remote receivers."""

    data = hass.data.setdefault(DOMAIN, {})
    if data.get(DATA_REMOTE_API_REGISTERED):
        return

    try:
        websocket_api = __import__(
            "homeassistant.components.websocket_api",
            fromlist=["async_register_command"],
        )
        vol = __import__("voluptuous")
    except ModuleNotFoundError:
        _LOGGER.debug("Home Assistant WebSocket API unavailable in test harness")
        return

    async def register_receiver(
        hass: Any,
        connection: Any,
        msg: dict[str, Any],
    ) -> None:
        device_id = str(msg.get("device_id", "")).strip()
        token = str(msg.get("token", "")).strip()
        receiver_name = _optional_text(msg.get("name"))

        if not _token_matches_config_entry(hass, device_id=device_id, token=token):
            connection.send_error(msg["id"], "unauthorized", "Receiver is not paired")
            return

        connection_id = str(id(connection))
        remote_registry(hass).register(
            device_id=device_id,
            connection=connection,
            connection_id=connection_id,
            receiver_name=receiver_name,
        )
        _register_disconnect_cleanup(hass, connection, device_id, connection_id)
        connection.send_result(
            msg["id"],
            {
                "accepted": True,
                "mode": "remote",
                "device_id": device_id,
            },
        )

    async def receive_status_response(
        hass: Any,
        connection: Any,
        msg: dict[str, Any],
    ) -> None:
        device_id = str(msg.get("device_id", "")).strip()
        request_id = int(msg.get("request_id", 0))
        status = msg.get("status")
        if not device_id or request_id <= 0 or not isinstance(status, dict):
            connection.send_error(
                msg["id"],
                "invalid_status_response",
                "Invalid receiver status response",
            )
            return
        accepted = remote_registry(hass).handle_status_response(
            device_id=device_id,
            request_id=request_id,
            status=status,
        )
        connection.send_result(
            msg["id"],
            {
                "accepted": accepted,
                "device_id": device_id,
                "request_id": request_id,
            },
        )

    register_receiver = websocket_api.websocket_command(
        {
            vol.Required("type"): WS_TYPE_REGISTER,
            vol.Required("device_id"): str,
            vol.Required("token"): str,
            vol.Optional("name"): str,
        }
    )(register_receiver)
    register_receiver = websocket_api.async_response(register_receiver)
    websocket_api.async_register_command(hass, register_receiver)

    receive_status_response = websocket_api.websocket_command(
        {
            vol.Required("type"): WS_TYPE_STATUS_RESPONSE,
            vol.Required("device_id"): str,
            vol.Required("request_id"): int,
            vol.Required("status"): dict,
        }
    )(receive_status_response)
    receive_status_response = websocket_api.async_response(receive_status_response)
    websocket_api.async_register_command(hass, receive_status_response)
    data[DATA_REMOTE_API_REGISTERED] = True


def _token_matches_config_entry(hass: Any, *, device_id: str, token: str) -> bool:
    if not device_id or not token:
        return False

    entries = getattr(hass, "data", {}).get(DOMAIN, {}).get("entries", {})
    for entry in entries.values():
        data = getattr(entry, "data", {})
        stored_token = str(data.get(CONF_TOKEN, ""))
        if data.get(CONF_DEVICE_ID) == device_id and compare_digest(
            stored_token,
            token,
        ):
            return True
    return False


def _register_disconnect_cleanup(
    hass: Any,
    connection: Any,
    device_id: str,
    connection_id: str,
) -> None:
    subscriptions = getattr(connection, "subscriptions", None)
    if not isinstance(subscriptions, dict):
        return

    def _unsubscribe() -> None:
        remote_registry(hass).unregister(device_id, connection_id)

    subscriptions[f"{DOMAIN}_remote_{device_id}"] = _unsubscribe


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
