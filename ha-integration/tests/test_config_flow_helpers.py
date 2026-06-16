"""Tests for config-flow helpers."""

# ruff: noqa: E402, I001

import sys
import types
from dataclasses import dataclass
from typing import Any

homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("homeassistant.config_entries")
voluptuous = types.ModuleType("voluptuous")


class FakeConfigFlow:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()


class FakeOptionsFlow:
    pass


config_entries.ConfigFlow = FakeConfigFlow  # type: ignore[attr-defined]
config_entries.OptionsFlow = FakeOptionsFlow  # type: ignore[attr-defined]
voluptuous.Schema = lambda schema: schema  # type: ignore[attr-defined]
voluptuous.Required = lambda key: key  # type: ignore[attr-defined]
voluptuous.Optional = lambda key, default=None: key  # type: ignore[attr-defined]
homeassistant.config_entries = config_entries  # type: ignore[attr-defined]
sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("voluptuous", voluptuous)

from custom_components.ha_tv_pip.config_flow import (  # noqa: E402
    _create_receiver_entry,
    _confirmed_receiver_name,
    _manual_port,
    _receiver_from_user_input,
    _receiver_from_zeroconf,
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
