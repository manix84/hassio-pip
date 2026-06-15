import asyncio
import sys
import types
from dataclasses import dataclass
from typing import Any

from custom_components.ha_tv_pip import async_setup_entry, async_unload_entry
from custom_components.ha_tv_pip.const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_VERSION,
    DOMAIN,
)


def test_domain_matches_integration_slug() -> None:
    assert DOMAIN == "ha_tv_pip"


@dataclass
class FakeConfigEntry:
    entry_id: str
    data: dict[str, Any]


class FakeDeviceRegistry:
    def __init__(self) -> None:
        self.created: dict[str, Any] | None = None

    def async_get_or_create(self, **kwargs: Any) -> None:
        self.created = kwargs


def test_config_entry_setup_registers_receiver_device() -> None:
    registry = FakeDeviceRegistry()
    homeassistant = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    device_registry.async_get = lambda hass: registry  # type: ignore[attr-defined]
    homeassistant.helpers = helpers  # type: ignore[attr-defined]
    helpers.device_registry = device_registry  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.helpers", helpers)
    sys.modules.setdefault("homeassistant.helpers.device_registry", device_registry)

    entry = FakeConfigEntry(
        entry_id="entry-1",
        data={
            CONF_DEVICE_ID: "49e3b07d8f4b7d65",
            CONF_HOST: "10.0.0.236",
            CONF_NAME: "Nursery TV",
            CONF_PORT: 8765,
            CONF_VERSION: "0.12.1",
        },
    )

    assert asyncio.run(async_setup_entry(hass=object(), entry=entry)) is True
    assert registry.created == {
        "config_entry_id": "entry-1",
        "identifiers": {(DOMAIN, "49e3b07d8f4b7d65")},
        "manufacturer": "HA TV PiP",
        "model": "Android TV Receiver",
        "name": "Nursery TV",
        "sw_version": "0.12.1",
        "configuration_url": "http://10.0.0.236:8765",
    }


def test_config_entry_unload_hook_returns_true() -> None:
    assert asyncio.run(async_unload_entry(hass=object(), entry=object())) is True
