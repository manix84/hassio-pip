"""Tests for HA TV PiP Home Assistant entities."""

import asyncio
from dataclasses import dataclass
from typing import Any

from custom_components.ha_tv_pip import binary_sensor, button, diagnostics, sensor
from custom_components.ha_tv_pip.client import ReceiverClientError, ReceiverStatus
from custom_components.ha_tv_pip.const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
)


@dataclass
class FakeEntry:
    entry_id: str
    data: dict[str, Any]


def _entry() -> FakeEntry:
    return FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_HOST: "10.0.0.236",
            CONF_NAME: "Nursery TV",
            CONF_PORT: 8765,
            CONF_TOKEN: "secret-token",
        },
    )


def _status() -> ReceiverStatus:
    return ReceiverStatus(
        app="HA TV PiP Receiver",
        version="0.24.0",
        device_id="device-1",
        device_name="Nursery TV",
        api_version=1,
        control_running=True,
        playback_state="playing",
        display_mode="overlay",
        pairing_state="paired",
        last_request={"method": "GET", "path": "/status", "status": 200},
        error=None,
        raw={"url": "http://example.test/private.m3u8", "playbackState": "playing"},
    )


def test_sensor_setup_adds_status_sensor() -> None:
    added: list[Any] = []

    asyncio.run(sensor.async_setup_entry(None, _entry(), added.extend))

    assert len(added) == 1
    assert added[0]._attr_unique_id == "device-1_status"


def test_binary_sensor_setup_adds_connected_sensor() -> None:
    added: list[Any] = []

    asyncio.run(binary_sensor.async_setup_entry(None, _entry(), added.extend))

    assert len(added) == 1
    assert added[0]._attr_unique_id == "device-1_connected"


def test_button_setup_adds_test_and_close_buttons() -> None:
    added: list[Any] = []

    asyncio.run(button.async_setup_entry(None, _entry(), added.extend))

    assert [entity._attr_unique_id for entity in added] == [
        "device-1_test",
        "device-1_close",
    ]


def test_status_sensor_updates_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(sensor, "async_get_receiver_status", fake_status)
    entity = sensor.ReceiverStatusSensor(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_native_value == "playing"
    assert entity._attr_extra_state_attributes["connected"] is True
    assert entity._attr_extra_state_attributes["display_mode"] == "overlay"


def test_connected_sensor_handles_unavailable_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        raise ReceiverClientError("cannot_connect")

    monkeypatch.setattr(binary_sensor, "async_get_receiver_status", fake_status)
    entity = binary_sensor.ReceiverConnectedBinarySensor(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is False
    assert entity._attr_extra_state_attributes == {"last_error": "cannot_connect"}


def test_test_button_sends_public_test_stream(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}

    async def fake_show(host: str, port: int, *, token: str, command: Any) -> None:
        captured.update(
            {
                "host": host,
                "port": port,
                "token": token,
                "title": command.title,
                "stream_type": command.stream_type,
            }
        )

    monkeypatch.setattr(button, "async_show_camera", fake_show)

    asyncio.run(button.ReceiverTestButton(_entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
        "title": "HA TV PiP Test",
        "stream_type": "hls",
    }


def test_close_button_sends_close_command(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}

    async def fake_close(host: str, port: int, *, token: str) -> bool:
        captured.update({"host": host, "port": port, "token": token})
        return True

    monkeypatch.setattr(button, "async_close_receiver", fake_close)

    asyncio.run(button.ReceiverCloseButton(_entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
    }


def test_diagnostics_redacts_token_and_url(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(diagnostics, "async_get_receiver_status", fake_status)

    result = asyncio.run(
        diagnostics.async_get_config_entry_diagnostics(None, _entry())
    )

    assert result["entry"][CONF_TOKEN] == diagnostics.REDACTED
    assert result["receiver_status"]["url"] == diagnostics.REDACTED
    assert result["receiver_error"] is None
