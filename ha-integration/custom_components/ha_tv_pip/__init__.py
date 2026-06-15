"""HA TV PiP Home Assistant integration.

The first integration slice supports Zeroconf discovery and config entry
creation. Device control, pairing, services, and entities are added in later
stages.
"""

# ruff: noqa: I001

from typing import Any

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_NAME, CONF_PORT, CONF_VERSION, DOMAIN

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
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    """Unload a HA TV PiP config entry."""

    return True
