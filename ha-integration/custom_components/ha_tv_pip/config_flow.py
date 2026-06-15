"""Config flow for HA TV PiP."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import voluptuous as vol  # type: ignore[import-not-found]
from homeassistant import config_entries  # type: ignore[import-not-found]

from .const import (
    CONF_API_VERSION,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PAIRING,
    CONF_PORT,
    CONF_VERSION,
    DEFAULT_PORT,
    DOMAIN,
)
from .discovery import ReceiverDiscovery, parse_discovery_properties

_LOGGER = logging.getLogger(__name__)


class ZeroconfDiscoveryInfo(Protocol):
    """Runtime shape Home Assistant passes to `async_step_zeroconf`."""

    host: str
    port: int | None
    properties: dict[str, Any]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for HA TV PiP."""

    VERSION = 1
    _discovered_receiver: ReceiverDiscovery | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle manual setup when Zeroconf discovery is unavailable."""

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                receiver = _receiver_from_user_input(user_input)
            except ValueError as error:
                errors["base"] = str(error)
            else:
                await self.async_set_unique_id(receiver.device_id)
                self._abort_if_unique_id_configured()
                return _create_receiver_entry(self, receiver)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfDiscoveryInfo,
    ) -> Any:
        """Handle a discovered HA TV PiP receiver."""

        _LOGGER.warning(
            "HA TV PiP Zeroconf flow triggered: host=%s port=%s properties=%s",
            discovery_info.host,
            discovery_info.port,
            dict(discovery_info.properties),
        )

        try:
            receiver = _receiver_from_zeroconf(discovery_info)
        except ValueError as error:
            _LOGGER.warning("HA TV PiP Zeroconf discovery rejected: %s", error)
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

        self._discovered_receiver = receiver
        self.context["title_placeholders"] = {"name": receiver.name}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> Any:
        """Ask the user to confirm a discovered HA TV PiP receiver."""

        receiver = self._discovered_receiver
        if receiver is None:
            return self.async_abort(reason="invalid_discovery")

        if user_input is not None:
            return _create_receiver_entry(self, receiver)

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                CONF_HOST: receiver.host,
                CONF_NAME: receiver.name,
                CONF_PORT: str(receiver.port),
            },
            errors={},
        )


def _create_receiver_entry(flow: ConfigFlow, receiver: ReceiverDiscovery) -> Any:
    """Create a Home Assistant config entry from receiver details."""

    flow.context["title_placeholders"] = {"name": receiver.name}
    return flow.async_create_entry(
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


def _receiver_from_zeroconf(discovery_info: ZeroconfDiscoveryInfo) -> ReceiverDiscovery:
    """Convert Home Assistant Zeroconf data into receiver discovery data."""

    return parse_discovery_properties(
        host=discovery_info.host,
        port=discovery_info.port,
        properties=dict(discovery_info.properties),
    )


def _receiver_from_user_input(user_input: dict[str, Any]) -> ReceiverDiscovery:
    """Convert manual setup data into receiver discovery data."""

    host = str(user_input.get(CONF_HOST, "")).strip()
    if not host:
        raise ValueError("invalid_host")

    port = _manual_port(user_input.get(CONF_PORT, DEFAULT_PORT))
    return ReceiverDiscovery(
        device_id=f"manual-{host}-{port}",
        name=f"HA TV PiP Receiver ({host})",
        host=host,
        port=port,
        version="unknown",
        pairing="disabled",
        api_version=1,
    )


def _manual_port(value: Any) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_port") from None

    if port < 1 or port > 65535:
        raise ValueError("invalid_port")

    return port
