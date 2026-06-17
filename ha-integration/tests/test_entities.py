"""Tests for HA TV PiP Home Assistant entities."""

import asyncio
from dataclasses import dataclass
from typing import Any

from custom_components.ha_tv_pip import (
    binary_sensor,
    button,
    diagnostics,
    sensor,
    switch,
)
from custom_components.ha_tv_pip.client import ReceiverClientError, ReceiverStatus
from custom_components.ha_tv_pip.const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
)


@dataclass
class FakeEntry:
    entry_id: str
    data: dict[str, Any]
    options: dict[str, Any] | None = None


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
        options={},
    )


def _entry_with_remote_options() -> FakeEntry:
    entry = _entry()
    entry.options = {
        CONF_REMOTE_HOME_ASSISTANT_URL: "https://example.ui.nabu.casa",
        CONF_REMOTE_ACCESS_TOKEN: "remote-token",
    }
    return entry


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
        launcher_visible=True,
        remote_status="connected",
        last_request={"method": "GET", "path": "/status", "status": 200},
        error=None,
        raw={
            "url": "http://example.test/private.m3u8",
            "fallbackUrl": "http://example.test/private.mjpeg",
            "playbackState": "playing",
            "playback": {
                "url": "http://example.test/nested-private.m3u8",
                "previewUrl": "http://example.test/private.jpg",
                "fallbackUrl": "http://example.test/nested-private.mjpeg",
                "streamType": "hls",
            },
            "remote": {
                "homeAssistantUrl": "https://example.ui.nabu.casa",
                "accessToken": "remote-token",
            },
            "pairing": {
                "state": "paired",
                "token": "local-token",
            },
        },
    )


def test_sensor_setup_adds_status_sensor() -> None:
    added: list[Any] = []

    asyncio.run(sensor.async_setup_entry(None, _entry(), added.extend))

    assert len(added) == 1
    assert added[0]._attr_unique_id == "device-1_status"
    assert added[0]._attr_translation_key == "status"


def test_binary_sensor_setup_adds_connected_sensor() -> None:
    added: list[Any] = []

    asyncio.run(binary_sensor.async_setup_entry(None, _entry(), added.extend))

    assert len(added) == 1
    assert added[0]._attr_unique_id == "device-1_connected"
    assert added[0]._attr_translation_key == "connected"


def test_button_setup_adds_open_test_and_close_buttons() -> None:
    added: list[Any] = []

    asyncio.run(button.async_setup_entry(None, _entry(), added.extend))

    assert [entity._attr_unique_id for entity in added] == [
        "device-1_open_launcher",
        "device-1_sync_remote_config",
        "device-1_test_pip",
        "device-1_close_pip",
    ]
    assert [entity._attr_name for entity in added] == [
        "Open Launcher",
        "Sync Remote Config",
        "Test PiP",
        "Close PiP",
    ]
    assert [entity._attr_translation_key for entity in added] == [
        "open_launcher",
        "sync_remote_config",
        "test_pip",
        "close_pip",
    ]
    assert added[0]._attr_entity_category == "config"
    assert added[1]._attr_entity_category == "config"
    assert not hasattr(added[2], "_attr_entity_category")
    assert not hasattr(added[3], "_attr_entity_category")


def test_switch_setup_adds_launcher_visibility_switch() -> None:
    added: list[Any] = []

    asyncio.run(switch.async_setup_entry(None, _entry(), added.extend))

    assert len(added) == 1
    assert added[0]._attr_unique_id == "device-1_hide_launcher"
    assert added[0]._attr_name == "Hide Launcher"
    assert added[0]._attr_translation_key == "hide_launcher"
    assert added[0]._attr_entity_category == "config"


def test_status_sensor_updates_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(sensor, "async_get_receiver_status", fake_status)
    entity = sensor.ReceiverStatusSensor(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_native_value == "playing"
    assert entity._attr_extra_state_attributes["connected"] is True
    assert entity._attr_extra_state_attributes["display_mode"] == "overlay"
    assert entity._attr_extra_state_attributes["remote_status"] == "connected"


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


def test_open_button_opens_receiver_management(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}

    async def fake_open(host: str, port: int, *, token: str) -> bool:
        captured.update({"host": host, "port": port, "token": token})
        return True

    monkeypatch.setattr(button, "async_open_receiver", fake_open)

    asyncio.run(button.ReceiverOpenButton(_entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
    }


def test_sync_remote_button_pushes_remote_config(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = object()
    entry = _entry_with_remote_options()

    async def fake_sync(received_hass: Any, received_entry: Any) -> bool:
        captured.update({"hass": received_hass, "entry": received_entry})
        return True

    monkeypatch.setattr(button, "async_sync_remote_setup", fake_sync)

    asyncio.run(button.ReceiverSyncRemoteButton(hass, entry).async_press())

    assert captured == {"hass": hass, "entry": entry}


def test_sync_remote_button_fails_without_remote_options() -> None:
    entity = button.ReceiverSyncRemoteButton(object(), _entry())

    try:
        asyncio.run(entity.async_press())
    except button.HomeAssistantError as error:
        assert "Configure remote receiver settings" in str(error)
    else:
        raise AssertionError("Expected HomeAssistantError")


def test_sync_remote_button_fails_when_push_fails(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_sync(received_hass: Any, received_entry: Any) -> bool:
        return False

    monkeypatch.setattr(button, "async_sync_remote_setup", fake_sync)
    entity = button.ReceiverSyncRemoteButton(object(), _entry_with_remote_options())

    try:
        asyncio.run(entity.async_press())
    except button.HomeAssistantError as error:
        assert "Could not send remote receiver settings" in str(error)
    else:
        raise AssertionError("Expected HomeAssistantError")


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


def test_launcher_switch_updates_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(switch, "async_get_receiver_status", fake_status)
    entity = switch.ReceiverLauncherSwitch(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is False


def test_launcher_switch_hides_launcher(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}

    async def fake_set_visible(
        host: str,
        port: int,
        *,
        token: str,
        visible: bool,
    ) -> bool:
        captured.update(
            {"host": host, "port": port, "token": token, "visible": visible}
        )
        return visible

    monkeypatch.setattr(switch, "async_set_launcher_visible", fake_set_visible)
    entity = switch.ReceiverLauncherSwitch(_entry())

    asyncio.run(entity.async_turn_on())

    assert entity._attr_is_on is True
    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
        "visible": False,
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
    assert result["receiver_status"]["fallbackUrl"] == diagnostics.REDACTED
    assert result["receiver_status"]["playback"]["url"] == diagnostics.REDACTED
    assert result["receiver_status"]["playback"]["previewUrl"] == diagnostics.REDACTED
    assert result["receiver_status"]["playback"]["fallbackUrl"] == diagnostics.REDACTED
    assert result["receiver_status"]["playback"]["streamType"] == "hls"
    assert (
        result["receiver_status"]["remote"]["homeAssistantUrl"]
        == diagnostics.REDACTED
    )
    assert result["receiver_status"]["remote"]["accessToken"] == diagnostics.REDACTED
    assert result["receiver_status"]["pairing"]["token"] == diagnostics.REDACTED
    assert result["receiver_error"] is None
