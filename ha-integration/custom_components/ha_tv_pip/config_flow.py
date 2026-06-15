"""Config flow for HA TV PiP."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries  # type: ignore[import-not-found]
from homeassistant.components.zeroconf import (  # type: ignore[import-not-found]
    ZeroconfServiceInfo,
)

from .const import (
    CONF_API_VERSION,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PAIRING,
    CONF_PORT,
    CONF_VERSION,
    DOMAIN,
)
from .discovery import ReceiverDiscovery, parse_discovery_properties


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for HA TV PiP."""

    VERSION = 1

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> Any:
        """Handle a discovered HA TV PiP receiver."""

        try:
            receiver = _receiver_from_zeroconf(discovery_info)
        except ValueError:
            return self.async_abort(reason="invalid_discovery")

        await self.async_set_unique_id(receiver.device_id)
        self._abort_if_unique_id_configured(
            updates={
                CONF_HOST: receiver.host,
                CONF_PORT: receiver.port,
                CONF_NAME: receiver.name,
                CONF_VERSION: receiver.version,
                CONF_PAIRING: receiver.pairing,
                CONF_API_VERSION: receiver.api_version,
            }
        )

        self.context["title_placeholders"] = {"name": receiver.name}
        return self.async_create_entry(
            title=receiver.name,
            data={
                CONF_DEVICE_ID: receiver.device_id,
                CONF_HOST: receiver.host,
                CONF_PORT: receiver.port,
                CONF_NAME: receiver.name,
                CONF_VERSION: receiver.version,
                CONF_PAIRING: receiver.pairing,
                CONF_API_VERSION: receiver.api_version,
            },
        )


def _receiver_from_zeroconf(discovery_info: ZeroconfServiceInfo) -> ReceiverDiscovery:
    """Convert Home Assistant Zeroconf data into receiver discovery data."""

    return parse_discovery_properties(
        host=discovery_info.host,
        port=discovery_info.port,
        properties=dict(discovery_info.properties),
    )
