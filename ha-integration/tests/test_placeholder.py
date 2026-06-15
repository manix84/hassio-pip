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


class FakeServices:
    def __init__(self) -> None:
        self.registered: list[dict[str, Any]] = []

    def has_service(self, domain: str, service: str) -> bool:
        return any(
            item["domain"] == domain and item["service"] == service
            for item in self.registered
        )

    def async_register(
        self,
        domain: str,
        service: str,
        handler: Any,
        **kwargs: Any,
    ) -> None:
        self.registered.append(
            {
                "domain": domain,
                "service": service,
                "handler": handler,
                "kwargs": kwargs,
            }
        )


class FakeHass:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.services = FakeServices()


def test_config_entry_setup_registers_receiver_device() -> None:
    registry = FakeDeviceRegistry()
    homeassistant = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    config_validation = types.ModuleType("homeassistant.helpers.config_validation")
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    voluptuous = sys.modules["voluptuous"]
    voluptuous.Any = lambda *args: args  # type: ignore[attr-defined]
    voluptuous.All = lambda *args: args  # type: ignore[attr-defined]
    voluptuous.Coerce = lambda value: value  # type: ignore[attr-defined]
    voluptuous.Range = lambda **kwargs: kwargs  # type: ignore[attr-defined]
    config_validation.entity_id = str  # type: ignore[attr-defined]
    device_registry.async_get = lambda hass: registry  # type: ignore[attr-defined]
    homeassistant.helpers = helpers  # type: ignore[attr-defined]
    helpers.config_validation = config_validation  # type: ignore[attr-defined]
    helpers.device_registry = device_registry  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.helpers", helpers)
    sys.modules.setdefault("homeassistant.helpers.config_validation", config_validation)
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

    hass = FakeHass()

    assert asyncio.run(async_setup_entry(hass=hass, entry=entry)) is True
    assert registry.created == {
        "config_entry_id": "entry-1",
        "identifiers": {(DOMAIN, "49e3b07d8f4b7d65")},
        "manufacturer": "HA TV PiP",
        "model": "Android TV Receiver",
        "name": "Nursery TV",
        "sw_version": "0.12.1",
        "configuration_url": "http://10.0.0.236:8765",
    }
    assert hass.data[DOMAIN]["entries"]["entry-1"] == entry
    assert hass.services.registered[0]["domain"] == DOMAIN
    assert hass.services.registered[0]["service"] == "show_camera"


def test_config_entry_unload_hook_removes_entry() -> None:
    hass = FakeHass()
    entry = FakeConfigEntry(entry_id="entry-1", data={})
    hass.data[DOMAIN] = {"entries": {"entry-1": entry}}

    assert asyncio.run(async_unload_entry(hass=hass, entry=entry)) is True
    assert hass.data[DOMAIN]["entries"] == {}
