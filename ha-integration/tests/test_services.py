"""Tests for HA TV PiP Home Assistant services."""

import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest

from custom_components.ha_tv_pip.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
)
from custom_components.ha_tv_pip.services import (
    ATTR_CAMERA_ENTITY,
    ATTR_DEVICE_ID,
    ATTR_DURATION_SECONDS,
    ATTR_ENTER_PIP,
    ATTR_RECEIVER_DEVICE_ID,
    ATTR_TITLE,
    ServiceValidationError,
    _absolute_stream_url,
    _camera_snapshot_url,
    _camera_title,
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


class FakeHass:
    def __init__(
        self,
        *,
        entries: list[FakeEntry],
        states: dict[str, FakeState] | None = None,
    ) -> None:
        self.config_entries = FakeConfigEntries(entries)
        self.states = FakeStates(states or {})


class FakeNetworkModule(types.ModuleType):
    def get_url(self, hass: Any, prefer_external: bool = False) -> str:
        return "http://10.0.0.2:8123"


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


def test_request_from_call_accepts_title_and_duration() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_DURATION_SECONDS: 10,
                ATTR_ENTER_PIP: False,
                ATTR_TITLE: "Doorbell",
            }
        )
    )

    assert request.duration_seconds == 10
    assert request.enter_pip is False
    assert request.title == "Doorbell"


def test_request_from_call_accepts_receiver_device_id_field() -> None:
    request = _request_from_call(
        FakeCall(
            data={
                ATTR_CAMERA_ENTITY: "camera.front_door",
                ATTR_RECEIVER_DEVICE_ID: "device-1",
            },
        )
    )

    assert request.device_ids == ("device-1",)


def test_resolve_receiver_uses_single_paired_entry_without_target() -> None:
    entry = FakeEntry(
        entry_id="entry-1",
        data={
            CONF_NAME: "Nursery TV",
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
        FakeEntry("entry-2", {CONF_HOST: "10.0.0.2", CONF_PORT: 8765, CONF_TOKEN: "b"}),
    ]

    with pytest.raises(ServiceValidationError) as error:
        _resolve_receiver(
            FakeHass(entries=entries),
            _request_from_call(
                FakeCall(data={ATTR_CAMERA_ENTITY: "camera.front_door"})
            ),
        )
    assert error.value.code == "multiple_receivers"


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


def test_camera_title_uses_friendly_name() -> None:
    hass = FakeHass(
        entries=[],
        states={"camera.front_door": FakeState({"friendly_name": "Front Door"})},
    )

    assert _camera_title(hass, "camera.front_door") == "Front Door"


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
