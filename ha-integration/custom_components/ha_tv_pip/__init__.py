"""HA TV PiP Home Assistant integration."""

# ruff: noqa: I001

from typing import Any

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_NAME, CONF_PORT, CONF_VERSION, DOMAIN
from .services import async_register_services

__all__ = ["DOMAIN"]


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    """Set up HA TV PiP from a config entry."""

    from homeassistant.helpers import device_registry as dr  # type: ignore[import-not-found]

    device_registry = dr.async_get(hass)
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
        manufacturer="HA TV PiP",
        model="Android TV Receiver",
        name=entry.data.get(CONF_NAME, "HA TV PiP Receiver"),
        sw_version=entry.data.get(CONF_VERSION),
        configuration_url=f"http://{host}:{port}" if host and port else None,
    )

    hass.data.setdefault(DOMAIN, {}).setdefault("entries", {})[entry.entry_id] = entry
    await async_register_services(hass)
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    """Unload a HA TV PiP config entry."""

    hass.data.get(DOMAIN, {}).get("entries", {}).pop(entry.entry_id, None)
    return True
