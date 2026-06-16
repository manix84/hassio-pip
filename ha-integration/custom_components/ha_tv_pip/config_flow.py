"""Config flow for HA TV PiP."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any, Protocol

import voluptuous as vol  # type: ignore[import-not-found]
from homeassistant import config_entries  # type: ignore[import-not-found]

from .client import ReceiverClientError, async_confirm_pairing, async_start_pairing
from .const import (
    CONF_API_VERSION,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PAIRING,
    CONF_PORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
    CONF_VERSION,
    DEFAULT_PORT,
    DOMAIN,
)
from .discovery import ReceiverDiscovery, parse_discovery_properties
from .remote_setup import (
    async_sync_remote_setup_values,
    suggested_remote_home_assistant_url,
)

_LOGGER = logging.getLogger(__name__)
PAIRING_CLIENT_ID = "home-assistant"
PAIRING_CLIENT_NAME = "Home Assistant"


class ZeroconfDiscoveryInfo(Protocol):
    """Runtime shape Home Assistant passes to `async_step_zeroconf`."""

    host: str
    port: int | None
    properties: dict[str, Any]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for HA TV PiP."""

    VERSION = 1
    _discovered_receiver: ReceiverDiscovery | None = None
    _pairing_receiver: ReceiverDiscovery | None = None

    @staticmethod
    def async_get_options_flow(config_entry: Any) -> Any:
        """Return the options flow for a configured receiver."""

        return ReceiverOptionsFlow(config_entry)

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
                if receiver.pairing == "disabled":
                    return _create_receiver_entry(self, receiver)
                self._pairing_receiver = receiver
                return await self.async_step_pair()

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

        _LOGGER.debug(
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
            confirmed_receiver = replace(
                receiver,
                name=_confirmed_receiver_name(user_input, fallback=receiver.name),
            )
            if confirmed_receiver.pairing == "disabled":
                return _create_receiver_entry(self, confirmed_receiver)
            self._pairing_receiver = confirmed_receiver
            return await self.async_step_pair()

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=receiver.name): str,
                }
            ),
            description_placeholders={
                CONF_HOST: receiver.host,
                CONF_NAME: receiver.name,
                CONF_PORT: str(receiver.port),
            },
            errors={},
        )

    async def async_step_pair(self, user_input: dict[str, Any] | None = None) -> Any:
        """Start receiver pairing and ask the user for the TV-visible code."""

        receiver = self._pairing_receiver
        if receiver is None:
            return self.async_abort(reason="invalid_discovery")

        errors: dict[str, str] = {}
        if user_input is None:
            try:
                await async_start_pairing(
                    receiver.host,
                    receiver.port,
                    client_id=PAIRING_CLIENT_ID,
                    client_name=PAIRING_CLIENT_NAME,
                )
            except ReceiverClientError as error:
                _LOGGER.warning("Unable to start HA TV PiP pairing: %s", error)
                errors["base"] = str(error)

        if user_input is not None:
            code = str(user_input.get("code", "")).strip()
            if not code:
                errors["code"] = "invalid_code"
            else:
                try:
                    result = await async_confirm_pairing(
                        receiver.host,
                        receiver.port,
                        client_id=PAIRING_CLIENT_ID,
                        client_name=PAIRING_CLIENT_NAME,
                        code=code,
                    )
                except ReceiverClientError as error:
                    _LOGGER.warning("Unable to confirm HA TV PiP pairing: %s", error)
                    errors["base"] = str(error)
                else:
                    return _create_receiver_entry(
                        self,
                        replace(receiver, pairing="paired"),
                        token=result.token,
                    )

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({vol.Required("code"): str}),
            description_placeholders={
                CONF_NAME: receiver.name,
                CONF_HOST: receiver.host,
                CONF_PORT: str(receiver.port),
            },
            errors=errors,
        )

class ReceiverOptionsFlow(config_entries.OptionsFlow):  # type: ignore[misc]
    """Options flow for remote receiver provisioning."""

    def __init__(self, config_entry: Any) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Configure remote receiver provisioning from Home Assistant."""

        errors: dict[str, str] = {}
        suggested_url = suggested_remote_home_assistant_url(self.hass)
        current_url = str(
            self.config_entry.options.get(
                CONF_REMOTE_HOME_ASSISTANT_URL,
                suggested_url,
            )
        ).strip()
        current_token = str(
            self.config_entry.options.get(CONF_REMOTE_ACCESS_TOKEN, "")
        ).strip()

        if user_input is not None:
            raw_remote_url = str(
                user_input.get(CONF_REMOTE_HOME_ASSISTANT_URL, "")
            ).strip()
            remote_token = str(user_input.get(CONF_REMOTE_ACCESS_TOKEN, "")).strip()
            remote_url = raw_remote_url or (suggested_url if remote_token else "")

            if bool(remote_url) != bool(remote_token):
                errors["base"] = "remote_fields_required"
            else:
                options: dict[str, str] = {}
                if remote_url and remote_token:
                    options[CONF_REMOTE_HOME_ASSISTANT_URL] = remote_url
                    options[CONF_REMOTE_ACCESS_TOKEN] = remote_token

                await async_sync_remote_setup_values(
                    self.hass,
                    self.config_entry,
                    remote_url,
                    remote_token,
                )
                return self.async_create_entry(title="", data=options)

            current_url = raw_remote_url or suggested_url
            current_token = remote_token

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_REMOTE_HOME_ASSISTANT_URL,
                        default=current_url,
                    ): str,
                    vol.Optional(
                        CONF_REMOTE_ACCESS_TOKEN,
                        default=current_token,
                    ): str,
                }
            ),
            description_placeholders={
                "suggested_url": suggested_url or "not configured"
            },
            errors=errors,
        )


def _create_receiver_entry(
    flow: ConfigFlow,
    receiver: ReceiverDiscovery,
    *,
    token: str | None = None,
) -> Any:
    """Create a Home Assistant config entry from receiver details."""

    data = {
        CONF_DEVICE_ID: receiver.device_id,
        CONF_HOST: receiver.host,
        CONF_PORT: receiver.port,
        CONF_NAME: receiver.name,
        CONF_VERSION: receiver.version,
        CONF_PAIRING: receiver.pairing,
        CONF_API_VERSION: receiver.api_version,
    }
    if token is not None:
        data[CONF_TOKEN] = token

    flow.context["title_placeholders"] = {"name": receiver.name}
    return flow.async_create_entry(
        title=receiver.name,
        data=data,
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
        pairing="required",
        api_version=1,
    )


def _confirmed_receiver_name(user_input: dict[str, Any], *, fallback: str) -> str:
    """Return the receiver name confirmed by the user."""

    name = str(user_input.get(CONF_NAME, "")).strip()
    return name or fallback


def _manual_port(value: Any) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_port") from None

    if port < 1 or port > 65535:
        raise ValueError("invalid_port")

    return port
