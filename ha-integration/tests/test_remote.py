"""Tests for remote HA TV PiP receiver transport."""

import asyncio
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest

from custom_components.ha_tv_pip.client import ShowCameraCommand
from custom_components.ha_tv_pip.const import CONF_DEVICE_ID, CONF_TOKEN, DOMAIN
from custom_components.ha_tv_pip.remote import (
    EVENT_RECEIVER_COMMAND,
    WS_TYPE_REGISTER,
    WS_TYPE_STATUS_RESPONSE,
    RemoteReceiverRegistry,
    async_setup_remote_api,
    remote_registry,
)


@dataclass
class FakeEntry:
    data: dict[str, Any]


class FakeHass:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}


class FakeConnection:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.results: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.subscriptions: dict[Any, Any] = {}

    def send_message(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def send_result(self, message_id: int, result: dict[str, Any]) -> None:
        self.results.append({"id": message_id, "result": result})

    def send_error(self, message_id: int, code: str, message: str) -> None:
        self.errors.append({"id": message_id, "code": code, "message": message})


def _install_fake_voluptuous(monkeypatch: pytest.MonkeyPatch) -> None:
    vol = types.ModuleType("voluptuous")
    vol.__dict__["Required"] = lambda value: value
    vol.__dict__["Optional"] = lambda value: value
    monkeypatch.setitem(sys.modules, "voluptuous", vol)


def test_remote_registry_sends_show_command_event() -> None:
    registry = RemoteReceiverRegistry()
    connection = FakeConnection()
    registry.register(
        device_id="device-1",
        connection=connection,
        connection_id="connection-1",
        receiver_name="Travel TV",
    )

    accepted = asyncio.run(
        registry.async_send_show(
            device_id="device-1",
            command=ShowCameraCommand(
                title="Front Door",
                url="https://home.example.test/api/hls/front-door",
                duration_seconds=30,
                enter_pip=True,
            ),
        )
    )

    assert accepted is True
    assert connection.messages == [
        {
            "id": 1,
            "type": "event",
            "event": {
                "event_type": EVENT_RECEIVER_COMMAND,
                "data": {
                    "command": "show",
                    "payload": {
                        "title": "Front Door",
                        "url": "https://home.example.test/api/hls/front-door",
                        "streamType": "hls",
                        "enterPip": True,
                        "durationSeconds": 30,
                    },
                },
            },
        }
    ]


def test_remote_registry_returns_false_when_receiver_not_connected() -> None:
    registry = RemoteReceiverRegistry()

    accepted = asyncio.run(
        registry.async_send_show(
            device_id="missing",
            command=ShowCameraCommand(
                title="Front Door",
                url="https://home.example.test/api/hls/front-door",
                duration_seconds=30,
                enter_pip=True,
            ),
        )
    )

    assert accepted is False


def test_remote_registry_sends_close_command_event() -> None:
    registry = RemoteReceiverRegistry()
    connection = FakeConnection()
    registry.register(
        device_id="device-1",
        connection=connection,
        connection_id="connection-1",
        receiver_name="Travel TV",
    )

    accepted = asyncio.run(registry.async_send_close(device_id="device-1"))

    assert accepted is True
    assert connection.messages == [
        {
            "id": 1,
            "type": "event",
            "event": {
                "event_type": EVENT_RECEIVER_COMMAND,
                "data": {
                    "command": "close",
                },
            },
        }
    ]


def test_remote_registry_returns_false_for_close_when_receiver_not_connected() -> None:
    registry = RemoteReceiverRegistry()

    accepted = asyncio.run(registry.async_send_close(device_id="missing"))

    assert accepted is False


def test_remote_registry_sends_status_command_and_resolves_response() -> None:
    async def run_test() -> None:
        registry = RemoteReceiverRegistry()
        connection = FakeConnection()
        registry.register(
            device_id="device-1",
            connection=connection,
            connection_id="connection-1",
            receiver_name="Travel TV",
        )

        task = asyncio.create_task(registry.async_get_status(device_id="device-1"))
        await asyncio.sleep(0)

        assert connection.messages == [
            {
                "id": 1,
                "type": "event",
                "event": {
                    "event_type": EVENT_RECEIVER_COMMAND,
                    "data": {
                        "command": "status",
                        "requestId": 1,
                    },
                },
            }
        ]
        accepted = registry.handle_status_response(
            device_id="device-1",
            request_id=1,
            status={
                "app": "HA TV PiP Receiver",
                "version": "1.30.0",
                "deviceId": "device-1",
                "deviceName": "Travel TV",
                "controlRunning": True,
                "playbackState": "idle",
                "displayMode": "idle",
            },
        )

        status = await task

        assert accepted is True
        assert status is not None
        assert status.version == "1.30.0"
        assert status.device_id == "device-1"
        assert status.playback_state == "idle"

    asyncio.run(run_test())


def test_remote_registry_returns_none_for_status_when_receiver_not_connected() -> None:
    registry = RemoteReceiverRegistry()

    status = asyncio.run(registry.async_get_status(device_id="missing"))

    assert status is None


def test_remote_websocket_registers_authenticated_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registered: dict[str, Any] = {}
    handlers: dict[str, Any] = {}
    websocket_api = types.ModuleType("homeassistant.components.websocket_api")
    _install_fake_voluptuous(monkeypatch)

    def websocket_command(schema: dict[Any, Any]) -> Any:
        registered["schema"] = schema
        websocket_type = str(schema["type"])

        def decorator(handler: Any) -> Any:
            handlers[websocket_type] = handler
            return handler

        return decorator

    def async_response(handler: Any) -> Any:
        return handler

    def async_register_command(hass: Any, handler: Any) -> None:
        registered.setdefault("registered_handlers", []).append(handler)

    websocket_api.websocket_command = websocket_command  # type: ignore[attr-defined]
    websocket_api.async_response = async_response  # type: ignore[attr-defined]
    websocket_api.async_register_command = async_register_command  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.websocket_api",
        websocket_api,
    )
    hass = FakeHass()
    hass.data[DOMAIN] = {
        "entries": {
            "entry-1": FakeEntry(
                {
                    CONF_DEVICE_ID: "device-1",
                    CONF_TOKEN: "secret-token",
                }
            )
        }
    }
    connection = FakeConnection()

    asyncio.run(async_setup_remote_api(hass))
    asyncio.run(
        handlers[WS_TYPE_REGISTER](
            hass,
            connection,
            {
                "id": 7,
                "type": WS_TYPE_REGISTER,
                "device_id": "device-1",
                "token": "secret-token",
                "name": "Travel TV",
            },
        )
    )

    assert connection.results == [
        {
            "id": 7,
            "result": {
                "accepted": True,
                "mode": "remote",
                "device_id": "device-1",
            },
        }
    ]
    assert remote_registry(hass).is_connected("device-1") is True
    assert WS_TYPE_STATUS_RESPONSE in handlers


def test_remote_websocket_rejects_unpaired_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registered: dict[str, Any] = {}
    handlers: dict[str, Any] = {}
    websocket_api = types.ModuleType("homeassistant.components.websocket_api")
    _install_fake_voluptuous(monkeypatch)

    def websocket_command(schema: dict[Any, Any]) -> Any:
        websocket_type = str(schema["type"])

        def decorator(handler: Any) -> Any:
            handlers[websocket_type] = handler
            return handler

        return decorator

    websocket_api.websocket_command = websocket_command  # type: ignore[attr-defined]
    websocket_api.async_response = lambda handler: handler  # type: ignore[attr-defined]
    websocket_api.async_register_command = (  # type: ignore[attr-defined]
        lambda hass, handler: registered.update({"handler": handler})
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.websocket_api",
        websocket_api,
    )
    hass = FakeHass()
    hass.data[DOMAIN] = {"entries": {}}
    connection = FakeConnection()

    asyncio.run(async_setup_remote_api(hass))
    asyncio.run(
        handlers[WS_TYPE_REGISTER](
            hass,
            connection,
            {
                "id": 8,
                "type": WS_TYPE_REGISTER,
                "device_id": "device-1",
                "token": "wrong-token",
            },
        )
    )

    assert connection.errors == [
        {
            "id": 8,
            "code": "unauthorized",
            "message": "Receiver is not paired",
        }
    ]
