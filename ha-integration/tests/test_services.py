"""Tests for HA TV PiP Home Assistant services."""

import asyncio
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest

from custom_components.ha_tv_pip.client import (
    ReceiverCapabilities,
    ReceiverClientError,
    ShowCameraCommand,
)
from custom_components.ha_tv_pip.const import (
    CONF_DEFAULT_DURATION_SECONDS,
    CONF_DEFAULT_HEIGHT,
    CONF_DEFAULT_POSITION,
    CONF_DEFAULT_SNAPSHOT_FALLBACK,
    CONF_DEFAULT_STREAM_TYPE,
    CONF_DEFAULT_WIDTH,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
)
from custom_components.ha_tv_pip.services import (
    ATTR_BACKGROUND_COLOR,
    ATTR_CAMERA_ENTITY,
    ATTR_DEVICE_ID,
    ATTR_DURATION_SECONDS,
    ATTR_ENTER_PIP,
    ATTR_HEIGHT,
    ATTR_MESSAGE,
    ATTR_MESSAGE_COLOR,
    ATTR_MESSAGE_SIZE,
    ATTR_POSITION,
    ATTR_RESTREAM_PROVIDER,
    ATTR_RESTREAM_URL,
    ATTR_SAVE,
    ATTR_SAVE_RECOMMENDATION,
    ATTR_SNAPSHOT_CAMERA_ENTITY,
    ATTR_SNAPSHOT_FALLBACK,
    ATTR_STREAM_CAMERA_ENTITY,
    ATTR_STREAM_TYPE,
    ATTR_TITLE,
    ATTR_TITLE_COLOR,
    ATTR_TITLE_SIZE,
    ATTR_WIDTH,
    ServiceValidationError,
    _absolute_stream_url,
    _async_show_camera_command,
    _camera_mjpeg_stream_url,
    _camera_snapshot_url,
    _camera_title,
    _notification_request_from_call,
    _request_from_call,
    _resolve_receiver,
    _validate_camera_entity,
)


@dataclass
class FakeCall:
    data: dict[str, Any]
    target: dict[str, Any] | None = None


@dataclass
class FakeEntry:
    entry_id: str
    data: dict[str, Any]
    options: dict[str, Any] | None = None


@dataclass
class FakeState:
    attributes: dict[str, Any]


class FakeStates:
    def __init__(self, states: dict[str, FakeState]) -> None:
        self._states = states

    def get(self, entity_id: str) -> FakeState | None:
        return self._states.get(entity_id)


class FakeConfigEntries:
    def __init__(self, entries: list[FakeEntry]) -> None:
        self._entries = entries

    def async_entries(self, domain: str) -> list[FakeEntry]:
        return self._entries

    def async_update_entry(self, entry: FakeEntry, *, options: dict[str, Any]) -> None:
        entry.options = options


class FakeHass:
    def __init__(
        self,
        *,
        entries: list[FakeEntry],
        states: dict[str, FakeState] | None = None,
    ) -> None:
        self.config_entries = FakeConfigEntries(entries)
        self.states = FakeStates(states or {})
        self.data: dict[str, Any] = {}


class FakeNetworkModule(types.ModuleType):
    def get_url(self, hass: Any, prefer_external: bool = False) -> str:
        if prefer_external:
            return "https://home.example.test"
        return "http://10.0.0.2:8123"


class FakeHomeAssistantError(Exception):
    """Fake Home Assistant error used by stream resolution tests."""


class FakeExceptionsModule(types.ModuleType):
    HomeAssistantError = FakeHomeAssistantError


class FakeCameraModule(types.ModuleType):
    def __init__(self, stream_url: str | None = "/api/hls/front-door") -> None:
        super().__init__("homeassistant.components.camera")
        self.stream_url = stream_url
        self.requested_entity_id: str | None = None

    async def async_request_stream(
        self,
        hass: Any,
        entity_id: str,
        stream_type: str,
    ) -> str | None:
        self.requested_entity_id = entity_id
        if self.stream_url == "raise":
            raise FakeHomeAssistantError("stream failed")
        return self.stream_url


def _capabilities(
    *,
    stream_types: tuple[str, ...] = ("hls", "mjpeg", "snapshot", "notification"),
    playable_fallback: bool = True,
    styled_notifications: bool = True,
    media_with_notification_text: bool = True,
) -> ReceiverCapabilities:
    return ReceiverCapabilities(
        capabilities_version=1,
        stream_types=stream_types,
        positions=("top_right", "top_left", "bottom_right", "bottom_left"),
        preview_image=True,
        playable_fallback=playable_fallback,
        native_picture_in_picture=True,
        overlay_fallback=True,
        styled_notifications=styled_notifications,
        media_with_notification_text=media_with_notification_text,
        launcher_management=True,
        local_pairing=True,
        remote_receiver_settings=True,
    )


@dataclass
class FakeDevice:
    config_entries: set[str]


class FakeDeviceRegistry:
    def __init__(self, devices: dict[str, FakeDevice]) -> None:
        self._devices = devices

    def async_get(self, device_id: str) -> FakeDevice | None:
        return self._devices.get(device_id)


def test_request_from_call_reads_target_and_defaults() -> None:
    request = _request_from_call(
        FakeCall(
            data={ATTR_CAMERA_ENTITY: "camera.front_door"},
            target={ATTR_DEVICE_ID: "device-1"},
        )
    )

    assert request.camera_entity == "camera.front_door"
    assert request.device_ids == ("device-1",)
    assert request.duration_seconds == 30
    assert request.enter_pip is True
    assert request.snapshot_camera_entity is None
    assert request.snapshot_fallback is True
    assert request.restream_provider is None
    assert request.restream_url is None
    assert request.stream_type == "auto"


def test_request_from_call_accepts_restream_source() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_RESTREAM_PROVIDER: "go2rtc",
                ATTR_RESTREAM_URL: (
                    "http://homeassistant.local:1984/api/stream.m3u8"
                    "?src=front_door"
                ),
            },
            target={ATTR_DEVICE_ID: "device-1"},
        )
    )

    assert request.restream_provider == "go2rtc"
    assert request.restream_url == (
        "http://homeassistant.local:1984/api/stream.m3u8?src=front_door"
    )
    assert request.restream_provider_explicit is True
    assert request.restream_url_explicit is True


def test_request_from_call_rejects_non_http_restream_url() -> None:
    with pytest.raises(ServiceValidationError, match="Restream URL"):
        _request_from_call(
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_RESTREAM_URL: "rtsp://camera.local/stream",
                },
                target={ATTR_DEVICE_ID: "device-1"},
            )
        )


def test_request_from_call_accepts_ha_target_device_id_from_data() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_DEVICE_ID: "ha-device-1",
            },
        )
    )

    assert request.device_ids == ("ha-device-1",)


def test_request_from_call_ignores_empty_ha_target_device_id_from_data() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_DEVICE_ID: None,
            },
        )
    )

    assert request.device_ids == ()


@pytest.mark.parametrize(
    "target_key,target_value",
    [
        ("entity_id", "sensor.not_a_receiver"),
        ("area_id", "living_room"),
        ("label_id", "security"),
        ("floor_id", "ground_floor"),
    ],
)
def test_request_from_call_rejects_non_device_targets(
    target_key: str,
    target_value: str,
) -> None:
    with pytest.raises(ServiceValidationError) as error:
        _request_from_call(
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={target_key: target_value},
            )
        )

    assert error.value.code == "unsupported_target_type"


def test_request_from_call_rejects_ha_injected_non_device_target_data() -> None:
    with pytest.raises(ServiceValidationError) as error:
        _request_from_call(
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    "area_id": "living_room",
                },
            )
        )

    assert error.value.code == "unsupported_target_type"


def test_request_from_call_accepts_title_and_duration() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_DURATION_SECONDS: 10,
                ATTR_ENTER_PIP: False,
                ATTR_SNAPSHOT_CAMERA_ENTITY: "camera.front_door_sub",
                ATTR_SNAPSHOT_FALLBACK: False,
                ATTR_STREAM_CAMERA_ENTITY: "camera.front_door_sub",
                ATTR_STREAM_TYPE: "snapshot",
                ATTR_TITLE: "Doorbell",
            }
        )
    )

    assert request.duration_seconds == 10
    assert request.enter_pip is False
    assert request.snapshot_camera_entity == "camera.front_door_sub"
    assert request.snapshot_fallback is False
    assert request.stream_camera_entity == "camera.front_door_sub"
    assert request.stream_type == "snapshot"
    assert request.title == "Doorbell"


def test_request_from_call_accepts_overlay_message_style() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_MESSAGE: "Someone is at the door",
                ATTR_POSITION: "bottom_left",
                ATTR_TITLE_COLOR: "#50BFF2",
                ATTR_TITLE_SIZE: 28,
                ATTR_MESSAGE_COLOR: "#fbf5f5",
                ATTR_MESSAGE_SIZE: 20,
                ATTR_BACKGROUND_COLOR: "#B30F0E0E",
                ATTR_WIDTH: 720,
                ATTR_HEIGHT: 360,
            }
        )
    )

    assert request.message == "Someone is at the door"
    assert request.position == "bottom_left"
    assert request.title_color == "#50BFF2"
    assert request.title_size == 28
    assert request.message_color == "#fbf5f5"
    assert request.message_size == 20
    assert request.background_color == "#B30F0E0E"
    assert request.width == 720
    assert request.height == 360


def test_request_from_call_rejects_invalid_stream_type() -> None:
    with pytest.raises(ServiceValidationError) as error:
        _request_from_call(
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_STREAM_TYPE: "webrtc",
                }
            )
        )

    assert error.value.code == "invalid_stream_type"


def test_notification_request_from_call_accepts_style_defaults_and_target() -> None:
    request = _notification_request_from_call(
        FakeCall(
            data={
                ATTR_TITLE: "Enhanced notifications",
                ATTR_MESSAGE: "Notifications can show text on the TV",
                ATTR_DURATION_SECONDS: 15,
                ATTR_ENTER_PIP: True,
                ATTR_POSITION: "bottom_right",
                ATTR_TITLE_COLOR: "#50BFF2",
                ATTR_TITLE_SIZE: 26,
                ATTR_MESSAGE_COLOR: "#fbf5f5",
                ATTR_MESSAGE_SIZE: 18,
                ATTR_BACKGROUND_COLOR: "#B30F0E0E",
                ATTR_WIDTH: 512,
                ATTR_HEIGHT: 240,
            },
            target={ATTR_DEVICE_ID: "device-1"},
        )
    )

    assert request.title == "Enhanced notifications"
    assert request.message == "Notifications can show text on the TV"
    assert request.duration_seconds == 15
    assert request.enter_pip is True
    assert request.position == "bottom_right"
    assert request.title_color == "#50BFF2"
    assert request.title_size == 26
    assert request.message_color == "#fbf5f5"
    assert request.message_size == 18
    assert request.background_color == "#B30F0E0E"
    assert request.width == 512
    assert request.height == 240
    assert request.device_ids == ("device-1",)


def test_notification_request_from_call_rejects_non_device_targets() -> None:
    with pytest.raises(ServiceValidationError) as error:
        _notification_request_from_call(
            FakeCall(data={}, target={"label_id": "security"}),
        )

    assert error.value.code == "unsupported_target_type"


def test_notification_request_rejects_invalid_color() -> None:
    with pytest.raises(ServiceValidationError) as error:
        _notification_request_from_call(
            FakeCall(data={ATTR_TITLE_COLOR: "blue"}),
        )

    assert error.value.code == "invalid_color"


def test_notification_request_rejects_invalid_overlay_size() -> None:
    with pytest.raises(ServiceValidationError) as error:
        _notification_request_from_call(
            FakeCall(data={ATTR_WIDTH: 200}),
        )

    assert error.value.code == "invalid_overlay_size"


def test_resolve_receiver_uses_single_paired_entry_without_target() -> None:
    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_NAME: "Nursery TV",
            CONF_DEVICE_ID: "device-1",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )

    receiver = _resolve_receiver(
        FakeHass(entries=[entry]),
        _request_from_call(FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})),
    )

    assert receiver.name == "Nursery TV"
    assert receiver.token == "token"


def test_resolve_receiver_requires_token() -> None:
    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
        },
    )

    with pytest.raises(ServiceValidationError) as error:
        _resolve_receiver(
            FakeHass(entries=[entry]),
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
        )
    assert error.value.code == "receiver_not_paired"


def test_resolve_receiver_requires_target_when_multiple_entries() -> None:
    entries = [
        FakeEntry("entry-1", {CONF_HOST: "10.0.0.1", CONF_PORT: 8765, CONF_TOKEN: "a"}),
        FakeEntry(
            "entry-2",
            {CONF_HOST: "10.0.0.2", CONF_PORT: 8765, CONF_TOKEN: "b"},
        ),
    ]

    with pytest.raises(ServiceValidationError) as error:
        _resolve_receiver(
            FakeHass(entries=entries),
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
        )
    assert error.value.code == "multiple_receivers"


def test_resolve_receiver_matches_home_assistant_target_device_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    device_registry_module = types.ModuleType("homeassistant.helpers.device_registry")
    registry = FakeDeviceRegistry(
        {"ha-device-2": FakeDevice(config_entries={"entry-2"})}
    )
    device_registry_module.async_get = lambda hass: registry  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.device_registry",
        device_registry_module,
    )
    entries = [
        FakeEntry(
            "entry-1",
            {
                CONF_DEVICE_ID: "receiver-1",
                CONF_HOST: "10.0.0.1",
                CONF_PORT: 8765,
                CONF_TOKEN: "a",
            },
        ),
        FakeEntry(
            "entry-2",
            {
                CONF_DEVICE_ID: "receiver-2",
                CONF_HOST: "10.0.0.2",
                CONF_PORT: 8765,
                CONF_TOKEN: "b",
            },
        ),
    ]

    receiver = _resolve_receiver(
        FakeHass(entries=entries),
        _request_from_call(
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "ha-device-2"},
            )
        ),
    )

    assert receiver.device_id == "receiver-2"
    assert receiver.host == "10.0.0.2"


def test_validate_camera_entity_requires_camera_domain_and_state() -> None:
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    _validate_camera_entity(hass, "camera.front_door")

    with pytest.raises(ServiceValidationError) as invalid_error:
        _validate_camera_entity(hass, "light.front_door")
    assert invalid_error.value.code == "invalid_camera_entity"

    with pytest.raises(ServiceValidationError) as missing_error:
        _validate_camera_entity(hass, "camera.missing")
    assert missing_error.value.code == "camera_not_found"


def test_absolute_stream_url_keeps_absolute_url() -> None:
    assert (
        _absolute_stream_url(FakeHass(entries=[]), "http://homeassistant.local/api/hls")
        == "http://homeassistant.local/api/hls"
    )


def test_absolute_stream_url_expands_relative_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_module = FakeNetworkModule("homeassistant.helpers.network")
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.network", network_module)

    assert (
        _absolute_stream_url(FakeHass(entries=[]), "/api/hls/front-door")
        == "http://10.0.0.2:8123/api/hls/front-door"
    )


def test_absolute_stream_url_can_prefer_external_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_module = FakeNetworkModule("homeassistant.helpers.network")
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.network", network_module)

    assert (
        _absolute_stream_url(
            FakeHass(entries=[]),
            "/api/hls/front-door",
            prefer_external=True,
        )
        == "https://home.example.test/api/hls/front-door"
    )


def test_camera_title_uses_friendly_name() -> None:
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    assert _camera_title(hass, "camera.front_door") == "Front Door"


def test_show_camera_command_auto_prefers_hls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={
            "camera.front_door": FakeState(
                {"friendly_name": "Front Door", "access_token": "snapshot-token"}
            )
        },
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_WIDTH: 800,
                        ATTR_HEIGHT: 450,
                    }
                )
            ),
            title="Front Door",
        )
    )

    assert command.stream_type == "hls"
    assert command.url == "http://10.0.0.2:8123/api/hls/front-door"
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )
    assert command.fallback_url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=snapshot-token"
    )
    assert command.fallback_stream_type == "mjpeg"
    assert command.width == 800
    assert command.height == 450
    assert command.message is None
    assert command.show_notification is False


def test_show_camera_command_can_use_separate_stream_camera_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    camera_module = FakeCameraModule("/api/hls/front-door-sub")
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        camera_module,
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={
            "camera.front_door": FakeState(
                {"friendly_name": "Front Door", "access_token": "main-token"}
            ),
            "camera.front_door_sub": FakeState(
                {"friendly_name": "Front Door Sub", "access_token": "sub-token"}
            ),
        },
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_CAMERA_ENTITY: "camera.front_door_sub",
                    }
                )
            ),
            title="Front Door",
        )
    )

    assert camera_module.requested_entity_id == "camera.front_door_sub"
    assert command.stream_type == "hls"
    assert command.url == "http://10.0.0.2:8123/api/hls/front-door-sub"
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=main-token"
    )
    assert command.fallback_url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door_sub"
        "?token=sub-token"
    )


def test_show_camera_command_can_use_restream_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={
            "camera.front_door": FakeState(
                {"friendly_name": "Front Door", "access_token": "main-token"}
            ),
        },
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_RESTREAM_PROVIDER: "go2rtc",
                        ATTR_RESTREAM_URL: (
                            "http://homeassistant.local:1984/api/stream.m3u8"
                            "?src=front_door"
                        ),
                    }
                )
            ),
            title="Front Door",
            capabilities=_capabilities(),
        )
    )

    assert command.stream_type == "hls"
    assert command.url == (
        "http://homeassistant.local:1984/api/stream.m3u8?src=front_door"
    )
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=main-token"
    )
    assert command.fallback_url is None


def test_show_camera_command_enables_notification_footer_for_custom_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={
            "camera.front_door": FakeState(
                {
                    "friendly_name": "Front Door",
                    "access_token": "snapshot-token",
                }
            )
        },
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_TITLE: "Doorbell",
                        ATTR_BACKGROUND_COLOR: "#B30F0E0E",
                        ATTR_SNAPSHOT_FALLBACK: False,
                    }
                )
            ),
            title="Doorbell",
        )
    )

    assert command.show_notification is True
    assert command.message is None
    assert command.position == "top_right"
    assert command.background_color == "#B30F0E0E"


def test_show_camera_command_uses_external_urls_for_remote_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={
            "camera.front_door": FakeState(
                {"friendly_name": "Front Door", "access_token": "snapshot-token"}
            )
        },
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
            prefer_external=True,
        )
    )

    assert command.url == "https://home.example.test/api/hls/front-door"
    assert command.preview_url == (
        "https://home.example.test/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_show_camera_service_prefers_connected_remote_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    sent: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return device_id == "device-1"

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            sent["device_id"] = device_id
            sent["url"] = command.url
            sent["preview_url"] = command.preview_url
            return True

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        sent["prefer_external"] = prefer_external
        sent["capabilities"] = capabilities
        return ShowCameraCommand(
            title=title,
            url="https://home.example.test/api/hls/front-door",
            duration_seconds=30,
            enter_pip=True,
            preview_url="https://home.example.test/api/camera_proxy/camera.front_door",
        )

    async def fail_local_show(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("local HTTP fallback should not be used")

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=None),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fail_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Travel TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"}),
        )
    )

    assert sent == {
        "prefer_external": True,
        "capabilities": None,
        "device_id": "device-1",
        "url": "https://home.example.test/api/hls/front-door",
        "preview_url": "https://home.example.test/api/camera_proxy/camera.front_door",
    }


def test_show_camera_service_falls_back_to_local_http_when_remote_disconnected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    sent: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        sent["prefer_external"] = prefer_external
        sent["capabilities"] = capabilities
        return ShowCameraCommand(
            title=title,
            url="http://10.0.0.2:8123/api/hls/front-door",
            duration_seconds=30,
            enter_pip=True,
        )

    async def fake_local_show(
        host: str,
        port: int,
        *,
        token: str,
        command: ShowCameraCommand,
    ) -> None:
        sent.update(
            {
                "host": host,
                "port": port,
                "token": token,
                "url": command.url,
            }
        )

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=None),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"}),
        )
    )

    assert sent == {
        "prefer_external": False,
        "capabilities": None,
        "host": "10.0.0.236",
        "port": 8765,
        "token": "token",
        "url": "http://10.0.0.2:8123/api/hls/front-door",
    }


def test_show_camera_service_applies_receiver_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    captured: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        captured.update(
            {
                "duration_seconds": request.duration_seconds,
                "height": request.height,
                "position": request.position,
                "snapshot_fallback": request.snapshot_fallback,
                "stream_type": request.stream_type,
                "width": request.width,
            }
        )
        return ShowCameraCommand(
            title=title,
            url="http://camera",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
        )

    async def fake_local_show(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=None),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={
            CONF_DEFAULT_DURATION_SECONDS: 42,
            CONF_DEFAULT_HEIGHT: 405,
            CONF_DEFAULT_POSITION: "bottom_left",
            CONF_DEFAULT_SNAPSHOT_FALLBACK: False,
            CONF_DEFAULT_STREAM_TYPE: "mjpeg_first",
            CONF_DEFAULT_WIDTH: 720,
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"}),
        )
    )

    assert captured == {
        "duration_seconds": 42,
        "height": 405,
        "position": "bottom_left",
        "snapshot_fallback": False,
        "stream_type": "mjpeg_first",
        "width": 720,
    }


def test_show_camera_service_keeps_explicit_values_over_receiver_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    captured: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        captured.update(
            {
                "duration_seconds": request.duration_seconds,
                "height": request.height,
                "position": request.position,
                "snapshot_fallback": request.snapshot_fallback,
                "stream_type": request.stream_type,
                "width": request.width,
            }
        )
        return ShowCameraCommand(
            title=title,
            url="http://camera",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
        )

    async def fake_local_show(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=None),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={
            CONF_DEFAULT_DURATION_SECONDS: 42,
            CONF_DEFAULT_HEIGHT: 405,
            CONF_DEFAULT_POSITION: "bottom_left",
            CONF_DEFAULT_SNAPSHOT_FALLBACK: False,
            CONF_DEFAULT_STREAM_TYPE: "mjpeg_first",
            CONF_DEFAULT_WIDTH: 720,
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_DURATION_SECONDS: 12,
                    ATTR_HEIGHT: 360,
                    ATTR_POSITION: "top_left",
                    ATTR_SNAPSHOT_FALLBACK: True,
                    ATTR_STREAM_TYPE: "hls",
                    ATTR_WIDTH: 640,
                }
            ),
        )
    )

    assert captured == {
        "duration_seconds": 12,
        "height": 360,
        "position": "top_left",
        "snapshot_fallback": True,
        "stream_type": "hls",
        "width": 640,
    }


def test_show_notification_service_applies_receiver_popup_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    sent: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_capabilities(receiver: Any) -> ReceiverCapabilities:
        return _capabilities()

    async def fake_local_show(
        host: str,
        port: int,
        *,
        token: str,
        command: ShowCameraCommand,
    ) -> None:
        sent.update(
            {
                "duration_seconds": command.duration_seconds,
                "height": command.height,
                "position": command.position,
                "width": command.width,
            }
        )

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(services, "_async_receiver_capabilities", fake_capabilities)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={
            CONF_DEFAULT_DURATION_SECONDS: 20,
            CONF_DEFAULT_HEIGHT: 240,
            CONF_DEFAULT_POSITION: "bottom_right",
            CONF_DEFAULT_WIDTH: 512,
        },
    )
    hass = FakeHass(entries=[entry])

    asyncio.run(
        services.async_handle_show_notification(
            hass,
            FakeCall(data={ATTR_TITLE: "Doorbell"}),
        )
    )

    assert sent == {
        "duration_seconds": 20,
        "height": 240,
        "position": "bottom_right",
        "width": 512,
    }
    command_result = hass.data["ha_tv_pip"]["last_command_result"]["entry-1"]
    assert command_result["command_type"] == "show_notification"
    assert command_result["status"] == "accepted"
    assert command_result["final_stream_type"] == "notification"
    assert command_result["transport"] == "local"


def test_set_camera_defaults_persists_per_camera_options() -> None:
    from custom_components.ha_tv_pip import services

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={},
    )
    hass = FakeHass(
        entries=[entry],
        states={
            "camera.front_door": FakeState({"friendly_name": "Front Door"}),
            "camera.front_door_sub": FakeState({"friendly_name": "Front Door Sub"}),
        },
    )

    result = asyncio.run(
        services.async_handle_set_camera_defaults(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_DURATION_SECONDS: 25,
                    ATTR_HEIGHT: 405,
                    ATTR_POSITION: "bottom_right",
                    ATTR_RESTREAM_PROVIDER: "go2rtc",
                    ATTR_RESTREAM_URL: (
                        "http://homeassistant.local:1984/api/stream.m3u8"
                        "?src=front_door"
                    ),
                    ATTR_SNAPSHOT_CAMERA_ENTITY: "camera.front_door_sub",
                    ATTR_SNAPSHOT_FALLBACK: True,
                    ATTR_STREAM_CAMERA_ENTITY: "camera.front_door_sub",
                    ATTR_STREAM_TYPE: "mjpeg_first",
                    ATTR_WIDTH: 720,
                },
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["accepted"] is True
    assert entry.options == {
        "camera_defaults": {
            "camera.front_door": {
                ATTR_DURATION_SECONDS: 25,
                ATTR_HEIGHT: 405,
                ATTR_POSITION: "bottom_right",
                ATTR_RESTREAM_PROVIDER: "go2rtc",
                ATTR_RESTREAM_URL: (
                    "http://homeassistant.local:1984/api/stream.m3u8"
                    "?src=front_door"
                ),
                ATTR_SNAPSHOT_CAMERA_ENTITY: "camera.front_door_sub",
                ATTR_SNAPSHOT_FALLBACK: True,
                ATTR_STREAM_CAMERA_ENTITY: "camera.front_door_sub",
                ATTR_STREAM_TYPE: "mjpeg_first",
                ATTR_WIDTH: 720,
            }
        }
    }


def test_show_camera_service_applies_per_camera_defaults_before_receiver_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    captured: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        captured.update(
            {
                "duration_seconds": request.duration_seconds,
                "height": request.height,
                "position": request.position,
                "restream_provider": request.restream_provider,
                "restream_url": request.restream_url,
                "snapshot_camera_entity": request.snapshot_camera_entity,
                "snapshot_fallback": request.snapshot_fallback,
                "stream_camera_entity": request.stream_camera_entity,
                "stream_type": request.stream_type,
                "width": request.width,
            }
        )
        return ShowCameraCommand(
            title=title,
            url="http://camera",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
        )

    async def fake_local_show(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=None),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={
            "camera_defaults": {
                "camera.front_door": {
                    ATTR_DURATION_SECONDS: 25,
                    ATTR_HEIGHT: 405,
                    ATTR_POSITION: "bottom_right",
                    ATTR_RESTREAM_PROVIDER: "go2rtc",
                    ATTR_RESTREAM_URL: (
                        "http://homeassistant.local:1984/api/stream.m3u8"
                        "?src=front_door"
                    ),
                    ATTR_SNAPSHOT_CAMERA_ENTITY: "camera.front_door_snapshot",
                    ATTR_SNAPSHOT_FALLBACK: False,
                    ATTR_STREAM_CAMERA_ENTITY: "camera.front_door_sub",
                    ATTR_STREAM_TYPE: "mjpeg_first",
                    ATTR_WIDTH: 720,
                }
            },
            CONF_DEFAULT_DURATION_SECONDS: 42,
            CONF_DEFAULT_POSITION: "top_left",
            CONF_DEFAULT_STREAM_TYPE: "hls",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={
            "camera.front_door": FakeState({"friendly_name": "Front Door"}),
            "camera.front_door_sub": FakeState({"friendly_name": "Front Door Sub"}),
            "camera.front_door_snapshot": FakeState({"friendly_name": "Snapshot"}),
        },
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"}),
        )
    )

    assert captured == {
        "duration_seconds": 25,
        "height": 405,
        "position": "bottom_right",
        "restream_provider": "go2rtc",
        "restream_url": (
            "http://homeassistant.local:1984/api/stream.m3u8?src=front_door"
        ),
        "snapshot_camera_entity": "camera.front_door_snapshot",
        "snapshot_fallback": False,
        "stream_camera_entity": "camera.front_door_sub",
        "stream_type": "mjpeg_first",
        "width": 720,
    }


def test_clear_camera_defaults_removes_stored_camera_options() -> None:
    from custom_components.ha_tv_pip import services

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
        options={"camera_defaults": {"camera.front_door": {ATTR_STREAM_TYPE: "hls"}}},
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    result = asyncio.run(
        services.async_handle_clear_camera_defaults(
            hass,
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["removed"] is True
    assert entry.options == {}


def test_camera_stream_test_stores_non_sensitive_compatibility_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(
            0,
            result=_capabilities(playable_fallback=False),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    result = asyncio.run(
        services.async_handle_test_camera_stream(
            hass,
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["recommended_stream_type"] == "mjpeg_first"
    assert (
        result["recommendation_reason"]
        == "mjpeg_first_reduces_receiver_decoder_risk"
    )
    assert result["restreaming_recommended"] is False
    assert "restreaming_provider" not in result
    assert result["stream_source"] == "camera_entity"
    assert result["recommended_defaults"] == {ATTR_STREAM_TYPE: "mjpeg_first"}
    assert result["tested_at"]
    assert result["results"] == [
        {"stream_type": "hls", "available": True},
        {"stream_type": "mjpeg", "available": True},
        {"stream_type": "snapshot", "available": True},
    ]
    assert "http" not in str(result)
    assert (
        hass.data["ha_tv_pip"]["camera_compatibility"]["entry-1"]["camera.front_door"]
        == result
    )


def test_camera_stream_test_recommends_auto_with_playable_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=_capabilities(playable_fallback=True)),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    result = asyncio.run(
        services.async_handle_test_camera_stream(
            hass,
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["recommended_stream_type"] == "auto"
    assert result["restreaming_recommended"] is False
    assert "restreaming_provider" not in result
    assert result["recommended_defaults"] == {ATTR_STREAM_TYPE: "auto"}
    assert (
        result["recommendation_reason"]
        == "hls_available_with_mjpeg_playable_fallback"
    )


def test_camera_stream_test_can_use_restream_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=_capabilities()),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule(None),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    result = asyncio.run(
        services.async_handle_test_camera_stream(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_RESTREAM_PROVIDER: "go2rtc",
                    ATTR_RESTREAM_URL: (
                        "http://homeassistant.local:1984/api/stream.m3u8"
                        "?src=front_door"
                    ),
                    ATTR_SAVE_RECOMMENDATION: True,
                },
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["recommended_stream_type"] == "hls"
    assert result["recommendation_reason"] == "hls_available"
    assert result["has_restream_url"] is True
    assert result["restream_provider"] == "go2rtc"
    assert result["stream_source"] == "restream_url"
    assert "homeassistant.local:1984" not in str(
        {
            key: value
            for key, value in result.items()
            if key not in {"recommended_defaults", "saved_defaults"}
        }
    )
    assert result["results"] == [
        {"stream_type": "hls", "available": True, "source": "restream_url"},
        {"stream_type": "mjpeg", "available": False},
        {"stream_type": "snapshot", "available": True},
    ]
    assert result["saved_defaults"] == {
        ATTR_RESTREAM_PROVIDER: "go2rtc",
        ATTR_RESTREAM_URL: (
            "http://homeassistant.local:1984/api/stream.m3u8?src=front_door"
        ),
        ATTR_STREAM_TYPE: "hls",
    }


def test_camera_stream_test_can_save_recommendation_as_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(
            0,
            result=_capabilities(playable_fallback=False),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    result = asyncio.run(
        services.async_handle_test_camera_stream(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_HEIGHT: 405,
                    ATTR_SAVE_RECOMMENDATION: True,
                    ATTR_SNAPSHOT_FALLBACK: True,
                    ATTR_WIDTH: 720,
                },
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["recommended_stream_type"] == "mjpeg_first"
    assert result["recommended_defaults"] == {
        ATTR_HEIGHT: 405,
        ATTR_SNAPSHOT_FALLBACK: True,
        ATTR_STREAM_TYPE: "mjpeg_first",
        ATTR_WIDTH: 720,
    }
    assert result["saved_as_defaults"] is True
    assert result["saved_defaults"] == {
        ATTR_HEIGHT: 405,
        ATTR_SNAPSHOT_FALLBACK: True,
        ATTR_STREAM_TYPE: "mjpeg_first",
        ATTR_WIDTH: 720,
    }
    assert entry.options == {
        "camera_defaults": {
            "camera.front_door": {
                ATTR_HEIGHT: 405,
                ATTR_SNAPSHOT_FALLBACK: True,
                ATTR_STREAM_TYPE: "mjpeg_first",
                ATTR_WIDTH: 720,
            }
        }
    }


def test_calibrate_camera_can_save_recommendation_with_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(
            0,
            result=_capabilities(playable_fallback=False),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("/api/hls/front-door"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    result = asyncio.run(
        services.async_handle_calibrate_camera(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_HEIGHT: 405,
                    ATTR_SAVE: True,
                    ATTR_SNAPSHOT_FALLBACK: True,
                    ATTR_WIDTH: 720,
                },
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["summary"] == {
        "compatible": True,
        "recommended_stream_type": "mjpeg_first",
        "recommendation_reason": "mjpeg_first_reduces_receiver_decoder_risk",
        "restreaming_recommended": False,
        "restreaming_reason": None,
        "restreaming_next_step": None,
        "restreaming_options": [],
        "saved": True,
        "next_step": "use_show_camera_without_repeating_defaults",
    }
    assert "restreaming_provider" not in result
    assert result["saved_as_defaults"] is True
    assert result["saved_defaults"] == {
        ATTR_HEIGHT: 405,
        ATTR_SNAPSHOT_FALLBACK: True,
        ATTR_STREAM_TYPE: "mjpeg_first",
        ATTR_WIDTH: 720,
    }
    assert entry.options == {
        "camera_defaults": {
            "camera.front_door": {
                ATTR_HEIGHT: 405,
                ATTR_SNAPSHOT_FALLBACK: True,
                ATTR_STREAM_TYPE: "mjpeg_first",
                ATTR_WIDTH: 720,
            }
        }
    }


def test_camera_stream_test_recommends_restreaming_for_snapshot_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(
            0,
            result=_capabilities(stream_types=("snapshot",)),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule(None),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    result = asyncio.run(
        services.async_handle_test_camera_stream(
            hass,
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["recommended_stream_type"] == "snapshot"
    assert result["recommendation_reason"] == "snapshot_available"
    assert result["restreaming_recommended"] is True
    assert (
        result["restreaming_reason"]
        == "snapshot_only_live_stream_restreaming_recommended"
    )
    assert result["restreaming_next_step"] == "configure_tv_safe_live_stream_source"
    assert result["restreaming_options"] == [
        "try_stream_camera_entity",
        "try_lower_resolution_profile",
        "try_mjpeg_or_h264_substream",
        "try_go2rtc_or_webrtc_bridge",
        "wait_for_transcoding_support",
    ]
    assert result["restreaming_provider"] == {
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
    assert result["recommended_defaults"] == {ATTR_STREAM_TYPE: "snapshot"}


def test_calibrate_camera_flags_restreaming_when_no_paths_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=_capabilities()),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule(None),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({})},
    )

    result = asyncio.run(
        services.async_handle_calibrate_camera(
            hass,
            FakeCall(
                data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    assert result["summary"] == {
        "compatible": False,
        "recommended_stream_type": None,
        "recommendation_reason": "no_compatible_stream_available",
        "restreaming_recommended": True,
        "restreaming_reason": "no_supported_stream_paths_restreaming_recommended",
        "restreaming_next_step": "check_camera_access_or_configure_tv_safe_source",
        "restreaming_options": [
            "check_camera_entity_access",
            "try_different_camera_entity",
            "try_lower_resolution_profile",
            "try_go2rtc_or_webrtc_bridge",
            "wait_for_transcoding_support",
        ],
        "restreaming_provider_status": "planned",
        "restreaming_provider_next_step": (
            "configure_tv_safe_live_stream_source"
        ),
        "saved": False,
        "next_step": "try_different_camera_entity_or_stream_source",
    }
    assert result["restreaming_recommended"] is True
    assert result["restreaming_provider"] == {
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
    assert "recommended_defaults" not in result


def test_show_camera_service_stores_last_camera_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        return ShowCameraCommand(
            title=title,
            url="http://private.example.test/camera.mjpeg",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
            stream_type="mjpeg",
            preview_url="http://private.example.test/preview.jpg",
            width=request.width,
            height=request.height,
        )

    async def fake_local_show(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=_capabilities()),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_STREAM_TYPE: "mjpeg",
                    ATTR_WIDTH: 720,
                    ATTR_HEIGHT: 405,
                },
                target={ATTR_DEVICE_ID: "device-1"},
            ),
        )
    )

    result = hass.data["ha_tv_pip"]["camera_last_result"]["entry-1"]
    updated_at = result.pop("updated_at")

    assert result == {
        "command_type": "show_camera",
        "camera_entity": "camera.front_door",
        "stream_camera_entity": "camera.front_door",
        "snapshot_camera_entity": "camera.front_door",
        "receiver": "Nursery TV",
        "receiver_device_id": "device-1",
        "requested_stream_type": "mjpeg",
        "stream_source": "camera_entity",
        "snapshot_fallback": True,
        "status": "accepted",
        "stage": "receiver_command",
        "transport": "local",
        "final_stream_type": "mjpeg",
        "has_preview": True,
        "has_playable_fallback": False,
        "width": 720,
        "height": 405,
        "has_notification_text": False,
    }
    assert "T" in updated_at
    assert hass.data["ha_tv_pip"]["last_command_result"]["entry-1"][
        "command_type"
    ] == "show_camera"
    assert "http" not in str(result)


def test_show_camera_service_stores_last_camera_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        return ShowCameraCommand(
            title=title,
            url="http://private.example.test/camera.m3u8",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
        )

    async def fake_local_show(*args: Any, **kwargs: Any) -> None:
        raise ReceiverClientError("decoder failed")

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(
        services,
        "_async_receiver_capabilities",
        lambda receiver: asyncio.sleep(0, result=_capabilities()),
    )
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    with pytest.raises(ServiceValidationError):
        asyncio.run(
            services.async_handle_show_camera(
                hass,
                FakeCall(
                    data={ATTR_CAMERA_ENTITY: "camera.front_door"},
                    target={ATTR_DEVICE_ID: "device-1"},
                ),
            )
        )

    result = hass.data["ha_tv_pip"]["camera_last_result"]["entry-1"]

    assert result["command_type"] == "show_camera"
    assert result["status"] == "failed"
    assert result["stage"] == "receiver_command"
    assert result["reason"] == "receiver_command_failed"
    assert result["detail"] == "decoder failed"
    assert result["final_stream_type"] == "hls"
    assert result["updated_at"]
    assert (
        hass.data["ha_tv_pip"]["last_command_result"]["entry-1"]["status"]
        == "failed"
    )
    assert "http" not in str(result)


def test_show_snapshot_service_rejects_receiver_without_snapshot_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_capabilities(receiver: Any) -> ReceiverCapabilities:
        return _capabilities(stream_types=("hls", "mjpeg"))

    async def fail_show(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unsupported snapshot should not be sent")

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(services, "_async_receiver_capabilities", fake_capabilities)
    monkeypatch.setattr(services, "async_show_camera", fail_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    with pytest.raises(ServiceValidationError) as error:
        asyncio.run(
            services.async_handle_show_snapshot(
                hass,
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"}),
            )
        )

    assert error.value.code == "receiver_capability_unavailable"


def test_show_notification_service_rejects_receiver_without_notification_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

    async def fake_capabilities(receiver: Any) -> ReceiverCapabilities:
        return _capabilities(stream_types=("hls", "snapshot"))

    async def fail_show(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unsupported notification should not be sent")

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(services, "_async_receiver_capabilities", fake_capabilities)
    monkeypatch.setattr(services, "async_show_camera", fail_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(entries=[entry])

    with pytest.raises(ServiceValidationError) as error:
        asyncio.run(
            services.async_handle_show_notification(
                hass,
                FakeCall(data={ATTR_TITLE: "Doorbell"}),
            )
        )

    assert error.value.code == "receiver_capability_unavailable"


def test_show_camera_service_strips_media_text_when_receiver_lacks_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services
    sent: dict[str, Any] = {}

    class FakeRemoteRegistry:
        def is_connected(self, device_id: str) -> bool:
            return False

        async def async_send_show(
            self,
            *,
            device_id: str,
            command: ShowCameraCommand,
        ) -> bool:
            return False

    async def fake_capabilities(receiver: Any) -> ReceiverCapabilities:
        return _capabilities(media_with_notification_text=False)

    async def fake_command(
        hass: Any,
        request: Any,
        *,
        title: str,
        prefer_external: bool = False,
        capabilities: ReceiverCapabilities | None = None,
    ) -> ShowCameraCommand:
        sent["request_title"] = request.title
        sent["request_message"] = request.message
        return ShowCameraCommand(
            title=title,
            url="http://camera",
            duration_seconds=request.duration_seconds,
            enter_pip=True,
            show_notification=request.title is not None or request.message is not None,
        )

    async def fake_local_show(
        host: str,
        port: int,
        *,
        token: str,
        command: ShowCameraCommand,
    ) -> None:
        sent["show_notification"] = command.show_notification

    monkeypatch.setattr(services, "remote_registry", lambda hass: FakeRemoteRegistry())
    monkeypatch.setattr(services, "_async_receiver_capabilities", fake_capabilities)
    monkeypatch.setattr(services, "_async_show_camera_command", fake_command)
    monkeypatch.setattr(services, "async_show_camera", fake_local_show)

    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "device-1",
            CONF_NAME: "Nursery TV",
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "token",
        },
    )
    hass = FakeHass(
        entries=[entry],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    asyncio.run(
        services.async_handle_show_camera(
            hass,
            FakeCall(
                data={
                    ATTR_CAMERA_ENTITY: "camera.front_door",
                    ATTR_TITLE: "Doorbell",
                    ATTR_MESSAGE: "Motion detected",
                }
            ),
        )
    )

    assert sent == {
        "request_title": None,
        "request_message": None,
        "show_notification": False,
    }


def test_show_camera_command_can_force_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_TYPE: "snapshot",
                    }
                )
            ),
            title="Front Door",
        ),
    )

    assert command.stream_type == "snapshot"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )
    assert command.preview_url is None


def test_show_camera_command_can_force_mjpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_TYPE: "mjpeg",
                    }
                )
            ),
            title="Front Door",
        ),
    )

    assert command.stream_type == "mjpeg"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=stream-token"
    )
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=stream-token"
    )


def test_show_camera_command_mjpeg_first_prefers_mjpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_TYPE: "mjpeg_first",
                    }
                )
            ),
            title="Front Door",
        ),
    )

    assert command.stream_type == "mjpeg"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=stream-token"
    )


def test_show_camera_command_auto_prefers_mjpeg_without_playable_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
            capabilities=_capabilities(playable_fallback=False),
        ),
    )

    assert command.stream_type == "mjpeg"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=stream-token"
    )


def test_show_camera_command_mjpeg_first_falls_back_to_hls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    camera_module = FakeCameraModule("/api/hls/front-door")
    monkeypatch.setitem(sys.modules, "homeassistant.components.camera", camera_module)
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    def fake_mjpeg_stream_url(
        hass: Any,
        entity_id: str,
        *,
        prefer_external: bool = False,
    ) -> str:
        raise ServiceValidationError("camera_mjpeg_unavailable")

    monkeypatch.setattr(services, "_camera_mjpeg_stream_url", fake_mjpeg_stream_url)
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_TYPE: "mjpeg_first",
                    }
                )
            ),
            title="Front Door",
        ),
    )

    assert camera_module.requested_entity_id == "camera.front_door"
    assert command.stream_type == "hls"
    assert command.url == "http://10.0.0.2:8123/api/hls/front-door"
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_show_camera_command_auto_falls_back_to_mjpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("raise"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
        )
    )

    assert command.stream_type == "mjpeg"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=snapshot-token"
    )
    assert command.preview_url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_show_camera_command_auto_falls_back_to_snapshot_when_mjpeg_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from custom_components.ha_tv_pip import services

    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("raise"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )

    def fake_mjpeg_stream_url(
        hass: Any,
        entity_id: str,
        *,
        prefer_external: bool = False,
    ) -> str:
        raise ServiceValidationError("camera_mjpeg_unavailable")

    monkeypatch.setattr(services, "_camera_mjpeg_stream_url", fake_mjpeg_stream_url)
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
        )
    )

    assert command.stream_type == "snapshot"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_show_camera_command_rejects_forced_unsupported_receiver_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    with pytest.raises(ServiceValidationError) as error:
        asyncio.run(
            _async_show_camera_command(
                hass,
                _request_from_call(
                    FakeCall(
                        data={
                            ATTR_CAMERA_ENTITY: "camera.front_door",
                            ATTR_STREAM_TYPE: "mjpeg",
                        }
                    )
                ),
                title="Front Door",
                capabilities=_capabilities(stream_types=("hls", "snapshot")),
            )
        )

    assert error.value.code == "receiver_capability_unavailable"


def test_show_camera_command_auto_skips_unsupported_hls_for_mjpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
            capabilities=_capabilities(stream_types=("mjpeg", "snapshot")),
        )
    )

    assert command.stream_type == "mjpeg"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy_stream/camera.front_door"
        "?token=stream-token"
    )


def test_show_camera_command_auto_uses_snapshot_when_only_snapshot_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
            capabilities=_capabilities(stream_types=("snapshot",)),
        )
    )

    assert command.stream_type == "snapshot"
    assert command.url == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_show_camera_command_auto_prefers_mjpeg_when_fallback_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    camera_module = FakeCameraModule("/api/hls/front-door")
    monkeypatch.setitem(sys.modules, "homeassistant.components.camera", camera_module)
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
            title="Front Door",
            capabilities=_capabilities(playable_fallback=False),
        )
    )

    assert command.stream_type == "mjpeg"
    assert command.fallback_url is None
    assert command.fallback_stream_type is None


def test_show_camera_command_mjpeg_first_skips_unsupported_mjpeg_for_hls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    camera_module = FakeCameraModule("/api/hls/front-door")
    monkeypatch.setitem(sys.modules, "homeassistant.components.camera", camera_module)
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    command = asyncio.run(
        _async_show_camera_command(
            hass,
            _request_from_call(
                FakeCall(
                    data={
                        ATTR_CAMERA_ENTITY: "camera.front_door",
                        ATTR_STREAM_TYPE: "mjpeg_first",
                    }
                )
            ),
            title="Front Door",
            capabilities=_capabilities(stream_types=("hls", "snapshot")),
        )
    )

    assert command.stream_type == "hls"
    assert command.url == "http://10.0.0.2:8123/api/hls/front-door"


def test_show_camera_command_forced_hls_does_not_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.components.camera",
        FakeCameraModule("raise"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.exceptions",
        FakeExceptionsModule("homeassistant.exceptions"),
    )
    monkeypatch.setitem(
        sys.modules,
        "homeassistant.helpers.network",
        FakeNetworkModule("homeassistant.helpers.network"),
    )
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    with pytest.raises(ServiceValidationError) as error:
        asyncio.run(
            _async_show_camera_command(
                hass,
                _request_from_call(
                    FakeCall(
                        data={
                            ATTR_CAMERA_ENTITY: "camera.front_door",
                            ATTR_STREAM_TYPE: "hls",
                        }
                    )
                ),
                title="Front Door",
            ),
        )

    assert error.value.code == "camera_stream_unavailable"


def test_camera_snapshot_url_uses_camera_proxy_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_module = FakeNetworkModule("homeassistant.helpers.network")
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.network", network_module)
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "snapshot-token"})},
    )

    assert _camera_snapshot_url(
        hass,
        "camera.front_door",
    ) == (
        "http://10.0.0.2:8123/api/camera_proxy/camera.front_door"
        "?token=snapshot-token"
    )


def test_camera_snapshot_url_requires_access_token() -> None:
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({})},
    )

    with pytest.raises(ServiceValidationError) as error:
        _camera_snapshot_url(hass, "camera.front_door")
    assert error.value.code == "snapshot_unavailable"


def test_camera_mjpeg_stream_url_uses_external_home_assistant_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_module = FakeNetworkModule("homeassistant.helpers.network")
    monkeypatch.setitem(sys.modules, "homeassistant.helpers.network", network_module)
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"access_token": "stream-token"})},
    )

    assert _camera_mjpeg_stream_url(
        hass,
        "camera.front_door",
        prefer_external=True,
    ) == (
        "https://home.example.test/api/camera_proxy_stream/camera.front_door"
        "?token=stream-token"
    )


def test_camera_mjpeg_stream_url_requires_access_token() -> None:
    hass = FakeHass(entries=[], states={"camera.front_door": FakeState({})})

    with pytest.raises(ServiceValidationError) as error:
        _camera_mjpeg_stream_url(hass, "camera.front_door")

    assert error.value.code == "camera_mjpeg_unavailable"
