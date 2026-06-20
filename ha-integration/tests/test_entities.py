"""Tests for HA TV PiP Home Assistant entities."""

import asyncio
from dataclasses import dataclass
from typing import Any

import custom_components.ha_tv_pip.binary_sensor as binary_sensor
import custom_components.ha_tv_pip.button as button
import custom_components.ha_tv_pip.diagnostics as diagnostics
import custom_components.ha_tv_pip.sensor as sensor
import custom_components.ha_tv_pip.switch as switch
from custom_components.ha_tv_pip.client import (
    ReceiverCapabilities,
    ReceiverClientError,
    ReceiverCompatibility,
    ReceiverRemoteStatus,
    ReceiverServiceStatus,
    ReceiverStatus,
)
from custom_components.ha_tv_pip.const import (
    CONF_CAMERA_DEFAULTS,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_PREFER_REMOTE_TRANSPORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
    DOMAIN,
)
from custom_components.ha_tv_pip.services import (
    CAMERA_COMPATIBILITY_KEY,
    CAMERA_LAST_RESULT_KEY,
    LAST_COMMAND_RESULT_KEY,
    LAST_COMMAND_RESULT_LISTENERS_KEY,
    store_last_command_result,
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


class FakeHass:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}


def _status() -> ReceiverStatus:
    return ReceiverStatus(
        app="HA TV PiP Receiver",
        version="0.24.0",
        device_id="device-1",
        device_name="Nursery TV",
        api_version=1,
        capabilities=ReceiverCapabilities(
            capabilities_version=1,
            stream_types=("hls", "mjpeg", "snapshot", "notification"),
            positions=("top_right", "bottom_left"),
            preview_image=True,
            playable_fallback=True,
            native_picture_in_picture=True,
            overlay_fallback=True,
            styled_notifications=True,
            media_with_notification_text=True,
            launcher_management=True,
            local_pairing=True,
            remote_receiver_settings=True,
        ),
        compatibility=ReceiverCompatibility(
            state="compatible",
            compatible=True,
            missing_features=(),
            warnings=(),
        ),
        service=ReceiverServiceStatus(
            running=True,
            foreground=True,
            start_count=2,
            last_start_reason="android.intent.action.MY_PACKAGE_REPLACED",
            last_started_at_millis=1_000,
            last_destroyed_at_millis=None,
            last_boot_receiver_action="android.intent.action.MY_PACKAGE_REPLACED",
            last_boot_receiver_at_millis=900,
        ),
        control_running=True,
        playback_state="playing",
        display_mode="overlay",
        stream_type="hls",
        pairing_state="paired",
        launcher_visible=True,
        remote_status="connected",
        remote=ReceiverRemoteStatus(
            status="connected",
            home_assistant_url="https://example.ui.nabu.casa",
            last_error=None,
            connected_at_millis=2_000,
            last_message_at_millis=3_000,
            connection_attempt_count=4,
            successful_connection_count=2,
            message_count=7,
            last_connection_attempt_at_millis=1_500,
            last_disconnected_at_millis=1_000,
            last_disconnect_reason="receiver reconnect",
        ),
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

    assert [entity._attr_unique_id for entity in added] == [
        "device-1_status",
        "device-1_display_mode",
        "device-1_stream_type",
        "device-1_last_error",
        "device-1_receiver_version",
        "device-1_receiver_compatibility",
        "device-1_last_command_result",
        "device-1_last_camera_compatibility",
        "device-1_last_camera_result",
        "device-1_restreaming_provider_status",
    ]
    assert [entity._attr_translation_key for entity in added] == [
        "status",
        "display_mode",
        "stream_type",
        "last_error",
        "receiver_version",
        "receiver_compatibility",
        "last_command_result",
        "last_camera_compatibility",
        "last_camera_result",
        "restreaming_provider_status",
    ]


def test_binary_sensor_setup_adds_connected_sensor() -> None:
    added: list[Any] = []

    asyncio.run(binary_sensor.async_setup_entry(None, _entry(), added.extend))

    assert [entity._attr_unique_id for entity in added] == [
        "device-1_connected",
        "device-1_remote_connected",
        "device-1_camera_restreaming_recommended",
    ]
    assert [entity._attr_translation_key for entity in added] == [
        "connected",
        "remote_connected",
        "camera_restreaming_recommended",
    ]


def test_button_setup_adds_open_test_and_close_buttons() -> None:
    added: list[Any] = []

    asyncio.run(button.async_setup_entry(None, _entry(), added.extend))

    assert [entity._attr_unique_id for entity in added] == [
        "device-1_open_launcher",
        "device-1_sync_remote_config",
        "device-1_refresh_status",
        "device-1_test_pip",
        "device-1_close_pip",
    ]
    assert [entity._attr_name for entity in added] == [
        "Open Launcher",
        "Sync Remote Config",
        "Refresh Status",
        "Test PiP",
        "Close PiP",
    ]
    assert [entity._attr_translation_key for entity in added] == [
        "open_launcher",
        "sync_remote_config",
        "refresh_status",
        "test_pip",
        "close_pip",
    ]
    assert added[0]._attr_entity_category == "config"
    assert added[1]._attr_entity_category == "config"
    assert not hasattr(added[2], "_attr_entity_category")
    assert not hasattr(added[3], "_attr_entity_category")
    assert not hasattr(added[4], "_attr_entity_category")


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
    assert entity._attr_extra_state_attributes["stream_type"] == "hls"
    assert entity._attr_extra_state_attributes["remote_status"] == "connected"
    assert entity._attr_extra_state_attributes["capabilities_version"] == 1
    assert entity._attr_extra_state_attributes["supported_stream_types"] == [
        "hls",
        "mjpeg",
        "snapshot",
        "notification",
    ]
    assert entity._attr_extra_state_attributes["supported_positions"] == [
        "top_right",
        "bottom_left",
    ]
    assert entity._attr_extra_state_attributes["supports_preview_image"] is True
    assert entity._attr_extra_state_attributes["supports_playable_fallback"] is True
    assert (
        entity._attr_extra_state_attributes["supports_native_picture_in_picture"]
        is True
    )
    assert entity._attr_extra_state_attributes["supports_overlay_fallback"] is True
    assert entity._attr_extra_state_attributes["supports_styled_notifications"] is True
    assert (
        entity._attr_extra_state_attributes["supports_media_with_notification_text"]
        is True
    )
    assert entity._attr_extra_state_attributes["supports_launcher_management"] is True
    assert entity._attr_extra_state_attributes["supports_local_pairing"] is True
    assert (
        entity._attr_extra_state_attributes["supports_remote_receiver_settings"]
        is True
    )
    assert (
        entity._attr_extra_state_attributes["remote_home_assistant_url_configured"]
        is True
    )
    assert entity._attr_extra_state_attributes["remote_last_error"] is None
    assert entity._attr_extra_state_attributes["remote_connected_at_millis"] == 2_000
    assert (
        entity._attr_extra_state_attributes["remote_last_message_at_millis"]
        == 3_000
    )
    assert (
        entity._attr_extra_state_attributes["remote_connection_attempt_count"]
        == 4
    )
    assert (
        entity._attr_extra_state_attributes["remote_successful_connection_count"]
        == 2
    )
    assert entity._attr_extra_state_attributes["remote_message_count"] == 7
    assert (
        entity._attr_extra_state_attributes[
            "remote_last_connection_attempt_at_millis"
        ]
        == 1_500
    )
    assert (
        entity._attr_extra_state_attributes["remote_last_disconnected_at_millis"]
        == 1_000
    )
    assert (
        entity._attr_extra_state_attributes["remote_last_disconnect_reason"]
        == "receiver reconnect"
    )
    assert entity._attr_extra_state_attributes["service_running"] is True
    assert entity._attr_extra_state_attributes["service_foreground"] is True
    assert entity._attr_extra_state_attributes["service_start_count"] == 2
    assert (
        entity._attr_extra_state_attributes["service_last_start_reason"]
        == "android.intent.action.MY_PACKAGE_REPLACED"
    )
    assert (
        entity._attr_extra_state_attributes["service_last_started_at_millis"]
        == 1_000
    )
    assert (
        entity._attr_extra_state_attributes["service_last_destroyed_at_millis"]
        is None
    )
    assert (
        entity._attr_extra_state_attributes["last_boot_receiver_action"]
        == "android.intent.action.MY_PACKAGE_REPLACED"
    )
    assert entity._attr_extra_state_attributes["last_boot_receiver_at_millis"] == 900


def test_restreaming_provider_status_sensor_reports_planned_state() -> None:
    entity = sensor.ReceiverRestreamingProviderStatusSensor(_entry())

    assert entity._attr_native_value == "planned"
    assert entity._attr_extra_state_attributes == {
        "enabled": False,
        "status": "planned",
        "configured_provider": None,
        "active_provider": None,
        "supported_providers": [],
        "planned_providers": ["go2rtc", "webrtc", "transcoding"],
        "recommended_current_paths": [
            "use_stream_camera_entity",
            "use_mjpeg_first",
            "use_snapshot_fallback",
            "use_camera_substream",
            "use_restream_url",
            "save_per_camera_defaults",
        ],
        "next_step": "configure_tv_safe_live_stream_source",
        "documentation_url": (
            "https://github.com/manix84/ha-tv-pip/blob/main/"
            "docs/camera-compatibility.md"
        ),
    }


def test_status_sensor_prefers_remote_transport_when_enabled(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
            }
        )
        return _status(), "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(sensor, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(sensor, "_async_get_receiver_status_command", fake_status)

    entity = sensor.ReceiverStatusSensor(entry, hass=hass)

    asyncio.run(entity.async_update())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
    }
    assert entity._attr_native_value == "playing"
    assert entity._attr_extra_state_attributes["transport"] == "remote"


def test_focused_status_sensors_update_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(sensor, "async_get_receiver_status", fake_status)

    display_mode = sensor.ReceiverDisplayModeSensor(_entry())
    stream_type = sensor.ReceiverStreamTypeSensor(_entry())
    last_error = sensor.ReceiverLastErrorSensor(_entry())
    version = sensor.ReceiverVersionSensor(_entry())
    compatibility = sensor.ReceiverCompatibilitySensor(_entry())

    asyncio.run(display_mode.async_update())
    asyncio.run(stream_type.async_update())
    asyncio.run(last_error.async_update())
    asyncio.run(version.async_update())
    asyncio.run(compatibility.async_update())

    assert display_mode._attr_native_value == "overlay"
    assert stream_type._attr_native_value == "hls"
    assert last_error._attr_native_value == "none"
    assert version._attr_native_value == "0.24.0"
    assert compatibility._attr_native_value == "compatible"
    assert (
        compatibility._attr_extra_state_attributes["summary"]
        == "Receiver supports the current integration feature set."
    )
    assert compatibility._attr_extra_state_attributes["compatible"] is True


def test_last_camera_result_sensor_reads_stored_result() -> None:
    class FakeHass:
        data = {
            DOMAIN: {
                CAMERA_LAST_RESULT_KEY: {
                    "entry-1": {
                        "camera_entity": "camera.front_door",
                        "final_stream_type": "mjpeg",
                        "status": "accepted",
                        "stream_source": "camera_entity",
                        "transport": "local",
                    }
                }
            }
        }

    entity = sensor.ReceiverLastCameraResultSensor(FakeHass(), _entry())

    asyncio.run(entity.async_update())

    assert entity._attr_native_value == "accepted"
    assert entity._attr_extra_state_attributes == {
        "camera_entity": "camera.front_door",
        "final_stream_type": "mjpeg",
        "status": "accepted",
        "stream_source": "camera_entity",
        "transport": "local",
    }


def test_last_command_result_sensor_reads_stored_result() -> None:
    class FakeResultHass:
        data = {
            DOMAIN: {
                LAST_COMMAND_RESULT_KEY: {
                    "entry-1": {
                        "command_type": "show_camera",
                        "final_stream_type": "mjpeg",
                        "status": "accepted",
                        "transport": "local",
                    }
                }
            }
        }

    entity = sensor.ReceiverLastCommandResultSensor(FakeResultHass(), _entry())

    asyncio.run(entity.async_update())

    assert entity._attr_native_value == "show_camera:accepted"
    assert entity._attr_extra_state_attributes == {
        "command_type": "show_camera",
        "final_stream_type": "mjpeg",
        "status": "accepted",
        "transport": "local",
    }


def test_last_command_result_sensor_refreshes_from_signal() -> None:
    class FakeResultHass:
        def __init__(self) -> None:
            self.data: dict[str, Any] = {
                DOMAIN: {LAST_COMMAND_RESULT_KEY: {"entry-1": {}}}
            }

    class TestableLastCommandResultSensor(sensor.ReceiverLastCommandResultSensor):
        def __init__(self, hass: Any, entry: Any) -> None:
            super().__init__(hass, entry)
            self.writes: list[str] = []

        def async_write_ha_state(self) -> None:
            self.writes.append(str(self._attr_native_value))

    hass = FakeResultHass()
    entity = TestableLastCommandResultSensor(hass, _entry())

    asyncio.run(entity.async_added_to_hass())
    assert (
        hass.data[DOMAIN][LAST_COMMAND_RESULT_LISTENERS_KEY]["entry-1"]
        == [entity._handle_command_result]
    )
    store_last_command_result(
        hass,
        "entry-1",
        {
            "command_type": "show_notification",
            "final_stream_type": "notification",
            "status": "accepted",
            "transport": "local",
        },
    )

    assert entity._attr_native_value == "show_notification:accepted"
    assert entity.writes == ["show_notification:accepted"]
    assert entity._attr_extra_state_attributes["final_stream_type"] == "notification"


def test_last_camera_compatibility_sensor_reads_latest_result() -> None:
    class FakeHass:
        data = {
            DOMAIN: {
                CAMERA_COMPATIBILITY_KEY: {
                    "entry-1": {
                        "camera.back_garden": {
                            "camera_entity": "camera.back_garden",
                            "recommended_stream_type": "hls",
                            "recommendation_reason": "hls_available",
                            "tested_at": "2026-06-18T10:00:00+00:00",
                        },
                        "camera.front_door": {
                            "camera_entity": "camera.front_door",
                            "recommended_stream_type": "mjpeg_first",
                            "recommendation_reason": (
                                "mjpeg_first_reduces_receiver_decoder_risk"
                            ),
                            "stream_source": "stream_camera_entity",
                            "tested_at": "2026-06-18T10:05:00+00:00",
                        },
                    }
                }
            }
        }

    entity = sensor.ReceiverLastCameraCompatibilitySensor(FakeHass(), _entry())

    asyncio.run(entity.async_update())

    assert entity._attr_native_value == "mjpeg_first"
    assert entity._attr_extra_state_attributes == {
        "camera_entity": "camera.front_door",
        "recommended_stream_type": "mjpeg_first",
        "recommendation_reason": "mjpeg_first_reduces_receiver_decoder_risk",
        "stream_source": "stream_camera_entity",
        "tested_at": "2026-06-18T10:05:00+00:00",
    }


def test_connected_sensor_handles_unavailable_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        raise ReceiverClientError("cannot_connect")

    monkeypatch.setattr(binary_sensor, "async_get_receiver_status", fake_status)
    entity = binary_sensor.ReceiverConnectedBinarySensor(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is False
    assert entity._attr_extra_state_attributes == {"last_error": "cannot_connect"}


def test_camera_restreaming_binary_sensor_reads_latest_result() -> None:
    class FakeHass:
        data = {
            DOMAIN: {
                CAMERA_COMPATIBILITY_KEY: {
                    "entry-1": {
                        "camera.back_garden": {
                            "camera_entity": "camera.back_garden",
                            "recommended_stream_type": "hls",
                            "recommendation_reason": "hls_available",
                            "restreaming_recommended": False,
                            "tested_at": "2026-06-18T10:00:00+00:00",
                        },
                        "camera.front_door": {
                            "camera_entity": "camera.front_door",
                            "recommended_stream_type": "snapshot",
                            "recommendation_reason": "snapshot_available",
                            "restreaming_recommended": True,
                            "restreaming_reason": (
                                "snapshot_only_live_stream_restreaming_recommended"
                            ),
                            "restreaming_next_step": (
                                "configure_tv_safe_live_stream_source"
                            ),
                            "restreaming_options": [
                                "try_stream_camera_entity",
                                "try_lower_resolution_profile",
                            ],
                            "tested_at": "2026-06-18T10:05:00+00:00",
                        },
                    }
                }
            }
        }

    entity = binary_sensor.ReceiverCameraRestreamingRecommendedBinarySensor(
        FakeHass(),
        _entry(),
    )

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is True
    assert entity._attr_extra_state_attributes == {
        "camera_entity": "camera.front_door",
        "recommended_stream_type": "snapshot",
        "recommendation_reason": "snapshot_available",
        "restreaming_reason": "snapshot_only_live_stream_restreaming_recommended",
        "restreaming_next_step": "configure_tv_safe_live_stream_source",
        "restreaming_options": [
            "try_stream_camera_entity",
            "try_lower_resolution_profile",
        ],
        "restreaming_provider_status": "planned",
        "restreaming_supported_providers": [],
        "restreaming_planned_providers": ["go2rtc", "webrtc", "transcoding"],
        "restreaming_recommended_current_paths": [
            "use_stream_camera_entity",
            "use_mjpeg_first",
            "use_snapshot_fallback",
            "use_camera_substream",
            "use_restream_url",
            "save_per_camera_defaults",
        ],
        "restreaming_documentation_url": (
            "https://github.com/manix84/ha-tv-pip/blob/main/"
            "docs/camera-compatibility.md"
        ),
        "tested_at": "2026-06-18T10:05:00+00:00",
    }


def test_remote_connected_sensor_updates_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(binary_sensor, "async_get_receiver_status", fake_status)
    entity = binary_sensor.ReceiverRemoteConnectedBinarySensor(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is True
    assert entity._attr_extra_state_attributes["remote_status"] == "connected"
    assert (
        entity._attr_extra_state_attributes["remote_home_assistant_url_configured"]
        is True
    )
    assert entity._attr_extra_state_attributes["remote_last_error"] is None
    assert (
        entity._attr_extra_state_attributes["remote_connection_attempt_count"]
        == 4
    )
    assert (
        entity._attr_extra_state_attributes["remote_successful_connection_count"]
        == 2
    )
    assert entity._attr_extra_state_attributes["remote_message_count"] == 7
    assert (
        entity._attr_extra_state_attributes["remote_last_disconnect_reason"]
        == "receiver reconnect"
    )


def test_remote_connected_sensor_prefers_remote_transport_when_enabled(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
            }
        )
        return _status(), "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(
        binary_sensor,
        "remote_registry",
        lambda hass: FakeRemoteRegistry(),
    )
    monkeypatch.setattr(
        binary_sensor,
        "_async_get_receiver_status_command",
        fake_status,
    )

    entity = binary_sensor.ReceiverRemoteConnectedBinarySensor(entry, hass=hass)

    asyncio.run(entity.async_update())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
    }
    assert entity._attr_is_on is True
    assert entity._attr_extra_state_attributes["transport"] == "remote"


def test_test_button_sends_public_test_stream(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_send(
        receiver: Any,
        remote: Any,
        command: Any,
        *,
        prefer_remote: bool,
    ) -> str:
        captured.update(
            {
                "host": receiver.host,
                "port": receiver.port,
                "token": receiver.token,
                "prefer_remote": prefer_remote,
                "title": command.title,
                "stream_type": command.stream_type,
            }
        )
        return "local"

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_send_receiver_command", fake_send)

    asyncio.run(button.ReceiverTestButton(hass, _entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
        "prefer_remote": False,
        "title": "HA TV PiP Test",
        "stream_type": "hls",
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "test_pip"
    assert result["status"] == "accepted"
    assert result["final_stream_type"] == "hls"


def test_test_button_prefers_remote_transport_when_enabled(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_send(
        receiver: Any,
        remote: Any,
        command: Any,
        *,
        prefer_remote: bool,
    ) -> str:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
                "title": command.title,
            }
        )
        return "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_send_receiver_command", fake_send)

    asyncio.run(button.ReceiverTestButton(hass, entry).async_press())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
        "title": "HA TV PiP Test",
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "test_pip"
    assert result["status"] == "accepted"
    assert result["transport"] == "remote"


def test_refresh_status_button_fetches_receiver_status(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        captured.update(
            {
                "host": receiver.host,
                "port": receiver.port,
                "prefer_remote": prefer_remote,
            }
        )
        return _status(), "local"

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_get_receiver_status_command", fake_status)

    asyncio.run(button.ReceiverRefreshStatusButton(hass, _entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "prefer_remote": False,
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "refresh_status"
    assert result["status"] == "accepted"
    assert result["transport"] == "local"


def test_refresh_status_button_prefers_remote_transport_when_enabled(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
            }
        )
        return _status(), "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_get_receiver_status_command", fake_status)

    asyncio.run(button.ReceiverRefreshStatusButton(hass, entry).async_press())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "refresh_status"
    assert result["status"] == "accepted"
    assert result["transport"] == "remote"


def test_refresh_status_button_reports_receiver_errors(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        raise ReceiverClientError("cannot_connect")

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_get_receiver_status_command", fake_status)
    hass = FakeHass()
    entity = button.ReceiverRefreshStatusButton(hass, _entry())

    try:
        asyncio.run(entity.async_press())
    except button.HomeAssistantError as error:
        assert "Could not refresh receiver status" in str(error)
    else:
        raise AssertionError("Expected HomeAssistantError")
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "refresh_status"
    assert result["status"] == "failed"


def test_open_button_opens_receiver_management(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    async def fake_open(host: str, port: int, *, token: str) -> bool:
        captured.update({"host": host, "port": port, "token": token})
        return True

    monkeypatch.setattr(button, "async_open_receiver", fake_open)

    asyncio.run(button.ReceiverOpenButton(hass, _entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "open_launcher"
    assert result["status"] == "accepted"


def test_sync_remote_button_pushes_remote_config(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()
    entry = _entry_with_remote_options()

    async def fake_sync(received_hass: Any, received_entry: Any) -> bool:
        captured.update({"hass": received_hass, "entry": received_entry})
        return True

    monkeypatch.setattr(button, "async_sync_remote_setup", fake_sync)

    asyncio.run(button.ReceiverSyncRemoteButton(hass, entry).async_press())

    assert captured == {"hass": hass, "entry": entry}
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "sync_remote_config"
    assert result["status"] == "accepted"


def test_sync_remote_button_fails_without_remote_options() -> None:
    hass = FakeHass()
    entity = button.ReceiverSyncRemoteButton(hass, _entry())

    try:
        asyncio.run(entity.async_press())
    except button.HomeAssistantError as error:
        assert "Configure remote receiver settings" in str(error)
    else:
        raise AssertionError("Expected HomeAssistantError")
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "sync_remote_config"
    assert result["status"] == "failed"
    assert result["reason"] == "remote_config_missing"


def test_sync_remote_button_fails_when_push_fails(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_sync(received_hass: Any, received_entry: Any) -> bool:
        return False

    monkeypatch.setattr(button, "async_sync_remote_setup", fake_sync)
    hass = FakeHass()
    entity = button.ReceiverSyncRemoteButton(hass, _entry_with_remote_options())

    try:
        asyncio.run(entity.async_press())
    except button.HomeAssistantError as error:
        assert "Could not send remote receiver settings" in str(error)
    else:
        raise AssertionError("Expected HomeAssistantError")
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "sync_remote_config"
    assert result["status"] == "failed"
    assert result["reason"] == "receiver_command_failed"


def test_close_button_sends_close_command(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_close(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[bool, str]:
        captured.update(
            {
                "host": receiver.host,
                "port": receiver.port,
                "token": receiver.token,
                "prefer_remote": prefer_remote,
            }
        )
        return True, "local"

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_close_receiver_command", fake_close)

    asyncio.run(button.ReceiverCloseButton(hass, _entry()).async_press())

    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "secret-token",
        "prefer_remote": False,
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "close_pip"
    assert result["status"] == "accepted"
    assert result["transport"] == "local"


def test_close_button_prefers_remote_transport_when_enabled(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_close(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[bool, str]:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
            }
        )
        return True, "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(button, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(button, "_async_close_receiver_command", fake_close)

    asyncio.run(button.ReceiverCloseButton(hass, entry).async_press())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
    }
    result = hass.data[DOMAIN][LAST_COMMAND_RESULT_KEY]["entry-1"]
    assert result["command_type"] == "close_pip"
    assert result["status"] == "accepted"
    assert result["transport"] == "remote"


def test_launcher_switch_updates_from_receiver(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_status(host: str, port: int) -> ReceiverStatus:
        return _status()

    monkeypatch.setattr(switch, "async_get_receiver_status", fake_status)
    entity = switch.ReceiverLauncherSwitch(_entry())

    asyncio.run(entity.async_update())

    assert entity._attr_is_on is False


def test_launcher_switch_prefers_remote_transport_when_enabled(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}
    hass = FakeHass()

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

    async def fake_status(
        receiver: Any,
        remote: Any,
        *,
        prefer_remote: bool,
    ) -> tuple[ReceiverStatus, str]:
        captured.update(
            {
                "device_id": receiver.device_id,
                "prefer_remote": prefer_remote,
            }
        )
        return _status(), "remote"

    entry = _entry()
    entry.options = {CONF_PREFER_REMOTE_TRANSPORT: True}

    monkeypatch.setattr(switch, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(switch, "_async_get_receiver_status_command", fake_status)

    entity = switch.ReceiverLauncherSwitch(entry, hass=hass)

    asyncio.run(entity.async_update())

    assert captured == {
        "device_id": "device-1",
        "prefer_remote": True,
    }
    assert entity._attr_is_on is False
    assert entity._attr_extra_state_attributes["transport"] == "remote"


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

    entry = _entry()
    entry.options = {
        CONF_CAMERA_DEFAULTS: {
            "camera.front_door": {
                "stream_type": "mjpeg_first",
                "restream_provider": "go2rtc",
                "restream_url": (
                    "http://homeassistant.local:1984/api/stream.m3u8"
                    "?src=front_door"
                ),
                "snapshot_fallback": True,
                "width": 720,
                "height": 405,
            }
        }
    }

    result = asyncio.run(diagnostics.async_get_config_entry_diagnostics(None, entry))

    assert result["entry"][CONF_TOKEN] == diagnostics.REDACTED
    assert result["integration"] == {
        "version": diagnostics._manifest_version(),
        "minimum_hacs_options_flow_version": "1.27.9",
    }
    assert result["camera_defaults"] == {
        "camera.front_door": {
            "stream_type": "mjpeg_first",
            "restream_provider": "go2rtc",
            "restream_url": diagnostics.REDACTED,
            "snapshot_fallback": True,
            "width": 720,
            "height": 405,
        }
    }
    assert result["camera_compatibility"] == {}
    assert result["camera_last_result"] == {}
    assert result["last_command_result"] == {}
    assert result["restreaming_providers"] == {
        "enabled": False,
        "status": "planned",
        "configured_provider": None,
        "active_provider": None,
        "supported_providers": [],
        "planned_providers": ["go2rtc", "webrtc", "transcoding"],
        "recommended_current_paths": [
            "use_stream_camera_entity",
            "use_mjpeg_first",
            "use_snapshot_fallback",
            "use_camera_substream",
            "use_restream_url",
            "save_per_camera_defaults",
        ],
        "next_step": "configure_tv_safe_live_stream_source",
        "documentation_url": (
            "https://github.com/manix84/ha-tv-pip/blob/main/"
            "docs/camera-compatibility.md"
        ),
    }
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
