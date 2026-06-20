"""Tests for config-flow helpers."""

# ruff: noqa: E402, I001

import asyncio
import sys
import types
from dataclasses import dataclass
from typing import Any

import pytest

homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("homeassistant.config_entries")
voluptuous = types.ModuleType("voluptuous")


class FakeConfigFlow:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()


class FakeOptionsFlow:
    config_entry: Any

    def async_show_form(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs: Any) -> dict[str, Any]:
        return {"type": "create_entry", **kwargs}


config_entries.ConfigFlow = FakeConfigFlow  # type: ignore[attr-defined]
config_entries.OptionsFlow = FakeOptionsFlow  # type: ignore[attr-defined]
voluptuous.Schema = lambda schema: schema  # type: ignore[attr-defined]
voluptuous.Required = lambda key: key  # type: ignore[attr-defined]
voluptuous.Optional = lambda key, default=None: key  # type: ignore[attr-defined]
voluptuous.Any = lambda *values: values  # type: ignore[attr-defined]
homeassistant.config_entries = config_entries  # type: ignore[attr-defined]
sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("voluptuous", voluptuous)

from custom_components.ha_tv_pip.const import (  # noqa: E402
    CONF_API_VERSION,
    CONF_DEFAULT_DURATION_SECONDS,
    CONF_DEFAULT_HEIGHT,
    CONF_DEFAULT_POSITION,
    CONF_DEFAULT_SNAPSHOT_FALLBACK,
    CONF_DEFAULT_STREAM_TYPE,
    CONF_DEFAULT_WIDTH,
    CONF_HOST,
    CONF_NAME,
    CONF_PAIRING,
    CONF_PORT,
    CONF_PREFER_REMOTE_TRANSPORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_SHOW_ADVANCED_OPTIONS,
    CONF_VERSION,
)
from custom_components.ha_tv_pip.config_flow import (  # noqa: E402
    ConfigFlow,
    ReceiverOptionsFlow,
    _create_receiver_entry,
    _confirmed_receiver_name,
    _manual_port,
    _receiver_discovery_updates,
    _receiver_from_user_input,
    _receiver_from_zeroconf,
    _select_dropdown,
    async_get_options_flow,
)
from custom_components.ha_tv_pip.discovery import ReceiverDiscovery


@dataclass
class FakeZeroconfDiscoveryInfo:
    host: str
    port: int | None
    properties: dict[str, Any]


def test_receiver_from_zeroconf_uses_duck_typed_discovery_info() -> None:
    receiver = _receiver_from_zeroconf(
        FakeZeroconfDiscoveryInfo(
            host="10.0.0.236",
            port=8765,
            properties={
                "id": b"49e3b07d8f4b7d65",
                "name": b"Nursery TV",
                "version": b"0.8.2",
                "pairing": b"disabled",
                "api": b"1",
            },
        )
    )

    assert receiver.device_id == "49e3b07d8f4b7d65"
    assert receiver.name == "Nursery TV"
    assert receiver.host == "10.0.0.236"
    assert receiver.port == 8765


def test_receiver_from_user_input_creates_manual_receiver() -> None:
    receiver = _receiver_from_user_input({"host": "10.0.0.236", "port": 8765})

    assert receiver.device_id == "manual-10.0.0.236-8765"
    assert receiver.name == "HA TV PiP Receiver (10.0.0.236)"
    assert receiver.host == "10.0.0.236"
    assert receiver.port == 8765
    assert receiver.version == "unknown"
    assert receiver.pairing == "required"
    assert receiver.api_version == 1


def test_manual_port_rejects_out_of_range_values() -> None:
    for value in ("not-a-port", 0, 65536):
        try:
            _manual_port(value)
        except ValueError as error:
            assert str(error) == "invalid_port"
        else:
            raise AssertionError(f"Expected invalid_port for {value}")


def test_confirmed_receiver_name_uses_user_value_or_fallback() -> None:
    assert (
        _confirmed_receiver_name({"name": "Kitchen TV"}, fallback="Nursery TV")
        == "Kitchen TV"
    )
    assert (
        _confirmed_receiver_name({"name": " "}, fallback="Nursery TV")
        == "Nursery TV"
    )


def test_create_receiver_entry_stores_pairing_token_when_present() -> None:
    class FakeFlow:
        context: dict[str, Any] = {}

        def async_create_entry(
            self,
            title: str,
            data: dict[str, Any],
        ) -> dict[str, Any]:
            return {"title": title, "data": data}

    entry = _create_receiver_entry(
        FakeFlow(),  # type: ignore[arg-type]
        ReceiverDiscovery(
            device_id="receiver-id",
            name="Nursery TV",
            host="10.0.0.236",
            port=8765,
            version="0.16.0",
            pairing="paired",
            api_version=1,
        ),
        token="secret-token",
    )

    assert entry["title"] == "Nursery TV"
    assert entry["data"]["pairing"] == "paired"
    assert entry["data"]["token"] == "secret-token"


def test_receiver_discovery_updates_repair_dhcp_address_changes() -> None:
    updates = _receiver_discovery_updates(
        ReceiverDiscovery(
            device_id="receiver-id",
            name="Nursery TV",
            host="10.0.0.240",
            port=8766,
            version="1.32.0",
            pairing="paired",
            api_version=1,
        )
    )

    assert updates == {
        CONF_API_VERSION: 1,
        CONF_HOST: "10.0.0.240",
        CONF_NAME: "Nursery TV",
        CONF_PAIRING: "paired",
        CONF_PORT: 8766,
        CONF_VERSION: "1.32.0",
    }


def test_options_flow_factory_is_exposed_at_module_and_class_level() -> None:
    entry = object()
    module_flow = async_get_options_flow(entry)
    class_flow = ConfigFlow.async_get_options_flow(entry)

    assert isinstance(module_flow, ReceiverOptionsFlow)
    assert isinstance(class_flow, ReceiverOptionsFlow)


def test_options_flow_init_step_returns_basic_defaults_form() -> None:
    flow = ReceiverOptionsFlow(types.SimpleNamespace(options={}))

    result = asyncio.run(flow.async_step_init())

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert list(result["data_schema"].keys()) == [
        CONF_DEFAULT_STREAM_TYPE,
        CONF_DEFAULT_DURATION_SECONDS,
        CONF_DEFAULT_SNAPSHOT_FALLBACK,
        CONF_PREFER_REMOTE_TRANSPORT,
        CONF_SHOW_ADVANCED_OPTIONS,
    ]


def test_options_flow_init_step_tolerates_missing_hass() -> None:
    flow = ReceiverOptionsFlow(types.SimpleNamespace(options={}))

    result = asyncio.run(flow.async_step_init())

    assert result["type"] == "form"
    assert result["step_id"] == "init"


def test_select_dropdown_uses_test_fallback_without_home_assistant_selector() -> None:
    assert _select_dropdown(("auto", "hls")) == ("auto", "hls")


def test_options_flow_basic_step_stores_common_defaults_and_preserves_advanced(
) -> None:
    flow = ReceiverOptionsFlow(
        types.SimpleNamespace(
            options={
                CONF_DEFAULT_HEIGHT: 360,
                CONF_DEFAULT_POSITION: "bottom_right",
                CONF_DEFAULT_WIDTH: 640,
                CONF_REMOTE_ACCESS_TOKEN: "remote-token",
                CONF_REMOTE_HOME_ASSISTANT_URL: "https://ha.example.test",
            }
        )
    )

    result = asyncio.run(
        flow.async_step_init(
            {
                CONF_DEFAULT_DURATION_SECONDS: 30,
                CONF_DEFAULT_SNAPSHOT_FALLBACK: False,
                CONF_DEFAULT_STREAM_TYPE: "mjpeg_first",
                CONF_PREFER_REMOTE_TRANSPORT: False,
                CONF_SHOW_ADVANCED_OPTIONS: False,
            }
        )
    )

    assert result == {
        "type": "create_entry",
        "title": "",
        "data": {
            CONF_DEFAULT_DURATION_SECONDS: 30,
            CONF_DEFAULT_HEIGHT: 360,
            CONF_DEFAULT_POSITION: "bottom_right",
            CONF_DEFAULT_SNAPSHOT_FALLBACK: False,
            CONF_DEFAULT_STREAM_TYPE: "mjpeg_first",
            CONF_DEFAULT_WIDTH: 640,
            CONF_PREFER_REMOTE_TRANSPORT: False,
            CONF_REMOTE_ACCESS_TOKEN: "remote-token",
            CONF_REMOTE_HOME_ASSISTANT_URL: "https://ha.example.test",
        },
    }


def test_options_flow_opens_advanced_step_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow = ReceiverOptionsFlow(types.SimpleNamespace(options={}))
    flow.hass = object()
    monkeypatch.setattr(
        "custom_components.ha_tv_pip.config_flow.suggested_remote_home_assistant_url",
        lambda hass: "https://example.ui.nabu.casa",
    )

    result = asyncio.run(
        flow.async_step_init(
            {
                CONF_DEFAULT_DURATION_SECONDS: 20,
                CONF_DEFAULT_SNAPSHOT_FALLBACK: True,
                CONF_DEFAULT_STREAM_TYPE: "auto",
                CONF_PREFER_REMOTE_TRANSPORT: False,
                CONF_SHOW_ADVANCED_OPTIONS: True,
            }
        )
    )

    assert result["type"] == "form"
    assert result["step_id"] == "advanced"
    assert result["description_placeholders"] == {
        "suggested_url": "https://example.ui.nabu.casa"
    }


def test_options_flow_advanced_step_saves_remote_setup_and_pending_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow = ReceiverOptionsFlow(types.SimpleNamespace(options={}))
    flow.hass = object()
    synced: dict[str, Any] = {}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.config_flow.suggested_remote_home_assistant_url",
        lambda hass: "https://example.ui.nabu.casa",
    )

    async def fake_sync(
        hass: Any,
        config_entry: Any,
        remote_url: str,
        remote_token: str,
    ) -> bool:
        synced["remote_url"] = remote_url
        synced["remote_token"] = remote_token
        return True

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.config_flow.async_sync_remote_setup_values",
        fake_sync,
    )

    first_result = asyncio.run(
        flow.async_step_init(
            {
                CONF_DEFAULT_DURATION_SECONDS: 20,
                CONF_DEFAULT_SNAPSHOT_FALLBACK: True,
                CONF_DEFAULT_STREAM_TYPE: "auto",
                CONF_PREFER_REMOTE_TRANSPORT: False,
                CONF_SHOW_ADVANCED_OPTIONS: True,
            }
        )
    )
    assert first_result["step_id"] == "advanced"

    result = asyncio.run(
        flow.async_step_advanced(
            {
                CONF_DEFAULT_HEIGHT: 405,
                CONF_DEFAULT_POSITION: "bottom_right",
                CONF_DEFAULT_WIDTH: 720,
                CONF_REMOTE_ACCESS_TOKEN: "remote-token",
                CONF_REMOTE_HOME_ASSISTANT_URL: "https://ha.example.test",
            }
        )
    )

    assert synced == {
        "remote_url": "https://ha.example.test",
        "remote_token": "remote-token",
    }
    assert result == {
        "type": "create_entry",
        "title": "",
        "data": {
            CONF_DEFAULT_DURATION_SECONDS: 20,
            CONF_DEFAULT_HEIGHT: 405,
            CONF_DEFAULT_POSITION: "bottom_right",
            CONF_DEFAULT_SNAPSHOT_FALLBACK: True,
            CONF_DEFAULT_STREAM_TYPE: "auto",
            CONF_DEFAULT_WIDTH: 720,
            CONF_PREFER_REMOTE_TRANSPORT: False,
            CONF_REMOTE_ACCESS_TOKEN: "remote-token",
            CONF_REMOTE_HOME_ASSISTANT_URL: "https://ha.example.test",
        },
    }


def test_options_flow_advanced_step_uses_suggested_remote_url_when_token_is_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flow = ReceiverOptionsFlow(types.SimpleNamespace(options={}))
    flow.hass = object()

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.config_flow.suggested_remote_home_assistant_url",
        lambda hass: "https://example.ui.nabu.casa",
    )

    async def fake_sync(
        hass: Any,
        config_entry: Any,
        remote_url: str,
        remote_token: str,
    ) -> bool:
        return True

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.config_flow.async_sync_remote_setup_values",
        fake_sync,
    )

    result = asyncio.run(
        flow.async_step_advanced(
            {
                CONF_DEFAULT_HEIGHT: 0,
                CONF_DEFAULT_POSITION: "top_right",
                CONF_DEFAULT_WIDTH: 0,
                CONF_REMOTE_ACCESS_TOKEN: "remote-token",
                CONF_REMOTE_HOME_ASSISTANT_URL: "",
            }
        )
    )

    assert result["data"][CONF_REMOTE_ACCESS_TOKEN] == "remote-token"
    assert (
        result["data"][CONF_REMOTE_HOME_ASSISTANT_URL]
        == "https://example.ui.nabu.casa"
    )
