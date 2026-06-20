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
    CONF_CAMERA_DEFAULTS,
    CONF_DEFAULT_DURATION_SECONDS,
    CONF_DEFAULT_HEIGHT,
    CONF_DEFAULT_POSITION,
    CONF_DEFAULT_SNAPSHOT_FALLBACK,
    CONF_DEFAULT_STREAM_TYPE,
    CONF_DEFAULT_WIDTH,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PAIRING,
    CONF_PORT,
    CONF_PREFER_REMOTE_TRANSPORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
    CONF_VERSION,
    DEFAULT_PORT,
    DOMAIN,
    NOTIFICATION_POSITIONS,
    STREAM_TYPE_AUTO,
    STREAM_TYPES,
)
from .discovery import ReceiverDiscovery, parse_discovery_properties
from .remote_setup import (
    async_sync_remote_setup_values,
    suggested_remote_home_assistant_url,
)

ha_selector: Any | None
try:
    ha_selector = __import__(
        "homeassistant.helpers.selector",
        fromlist=["SelectSelector"],
    )
except (ImportError, ModuleNotFoundError):
    ha_selector = None

_LOGGER = logging.getLogger(__name__)
PAIRING_CLIENT_ID = "home-assistant"
PAIRING_CLIENT_NAME = "Home Assistant"


class ZeroconfDiscoveryInfo(Protocol):
    """Runtime shape Home Assistant passes to `async_step_zeroconf`."""

    host: str
    port: int | None
    properties: dict[str, Any]


def async_get_options_flow(config_entry: Any) -> Any:
    """Return the options flow for a configured receiver."""

    return ReceiverOptionsFlow(config_entry)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg,misc]
    """Handle a config flow for HA TV PiP."""

    VERSION = 1
    _discovered_receiver: ReceiverDiscovery | None = None
    _pairing_receiver: ReceiverDiscovery | None = None

    @staticmethod
    def async_get_options_flow(config_entry: Any) -> Any:
        """Return the options flow for a configured receiver."""

        return async_get_options_flow(config_entry)

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
            updates=_receiver_discovery_updates(receiver)
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
    """Options flow for receiver defaults and remote receiver provisioning."""

    def __init__(self, config_entry: Any) -> None:
        """Initialize the options flow with a Home Assistant config entry.

        Home Assistant's newer OptionsFlow exposes `self.config_entry` after the
        flow manager attaches runtime context. Keeping a local reference makes
        the flow tolerant of older Core versions that do not expose that helper.
        """

        self._config_entry = config_entry

    @property
    def _entry(self) -> Any:
        """Return the active config entry across supported Home Assistant versions."""

        try:
            return self.config_entry
        except (AttributeError, ValueError):
            return self._config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Configure receiver defaults and remote provisioning from Home Assistant."""

        errors: dict[str, str] = {}
        entry = self._entry
        hass = getattr(self, "hass", None)
        suggested_url = suggested_remote_home_assistant_url(hass)
        current_url = str(
            entry.options.get(
                CONF_REMOTE_HOME_ASSISTANT_URL,
                suggested_url,
            )
        ).strip()
        current_token = str(
            entry.options.get(CONF_REMOTE_ACCESS_TOKEN, "")
        ).strip()
        current_stream_type = str(
            entry.options.get(CONF_DEFAULT_STREAM_TYPE, STREAM_TYPE_AUTO)
        ).strip()
        if current_stream_type not in STREAM_TYPES:
            current_stream_type = STREAM_TYPE_AUTO
        current_position = str(
            entry.options.get(CONF_DEFAULT_POSITION, "top_right")
        ).strip()
        if current_position not in NOTIFICATION_POSITIONS:
            current_position = "top_right"
        current_duration = (
            _optional_default_int(
                entry.options.get(CONF_DEFAULT_DURATION_SECONDS),
                minimum=0,
                maximum=3600,
            )
            or 0
        )
        current_width = (
            _optional_default_int(
                entry.options.get(CONF_DEFAULT_WIDTH),
                minimum=0,
                maximum=1600,
            )
            or 0
        )
        current_height = (
            _optional_default_int(
                entry.options.get(CONF_DEFAULT_HEIGHT),
                minimum=0,
                maximum=900,
            )
            or 0
        )
        current_snapshot_fallback = bool(
            entry.options.get(CONF_DEFAULT_SNAPSHOT_FALLBACK, True)
        )
        current_prefer_remote_transport = bool(
            entry.options.get(CONF_PREFER_REMOTE_TRANSPORT, False)
        )

        if user_input is not None:
            raw_remote_url = str(
                user_input.get(CONF_REMOTE_HOME_ASSISTANT_URL, "")
            ).strip()
            remote_token = str(user_input.get(CONF_REMOTE_ACCESS_TOKEN, "")).strip()
            remote_url = (raw_remote_url or suggested_url) if remote_token else ""
            default_stream_type = str(
                user_input.get(CONF_DEFAULT_STREAM_TYPE, STREAM_TYPE_AUTO)
            ).strip()
            default_position = str(
                user_input.get(CONF_DEFAULT_POSITION, "top_right")
            ).strip()
            default_duration = _optional_default_int(
                user_input.get(CONF_DEFAULT_DURATION_SECONDS),
                minimum=0,
                maximum=3600,
            )
            default_width = _optional_default_int(
                user_input.get(CONF_DEFAULT_WIDTH),
                minimum=0,
                maximum=1600,
            )
            default_height = _optional_default_int(
                user_input.get(CONF_DEFAULT_HEIGHT),
                minimum=0,
                maximum=900,
            )
            default_snapshot_fallback = bool(
                user_input.get(CONF_DEFAULT_SNAPSHOT_FALLBACK, True)
            )
            prefer_remote_transport = bool(
                user_input.get(CONF_PREFER_REMOTE_TRANSPORT, False)
            )

            if bool(remote_url) != bool(remote_token):
                errors["base"] = "remote_fields_required"
            elif default_stream_type not in STREAM_TYPES:
                errors[CONF_DEFAULT_STREAM_TYPE] = "invalid_default_stream_type"
            elif default_position not in NOTIFICATION_POSITIONS:
                errors[CONF_DEFAULT_POSITION] = "invalid_default_position"
            elif default_duration is None:
                errors[CONF_DEFAULT_DURATION_SECONDS] = "invalid_default_duration"
            elif default_width is None:
                errors[CONF_DEFAULT_WIDTH] = "invalid_default_overlay_size"
            elif default_height is None:
                errors[CONF_DEFAULT_HEIGHT] = "invalid_default_overlay_size"
            else:
                options: dict[str, Any] = {
                    CONF_DEFAULT_STREAM_TYPE: default_stream_type,
                    CONF_DEFAULT_POSITION: default_position,
                    CONF_DEFAULT_SNAPSHOT_FALLBACK: default_snapshot_fallback,
                    CONF_PREFER_REMOTE_TRANSPORT: prefer_remote_transport,
                }
                if default_duration > 0:
                    options[CONF_DEFAULT_DURATION_SECONDS] = default_duration
                if default_width > 0:
                    options[CONF_DEFAULT_WIDTH] = default_width
                if default_height > 0:
                    options[CONF_DEFAULT_HEIGHT] = default_height
                if CONF_CAMERA_DEFAULTS in entry.options:
                    options[CONF_CAMERA_DEFAULTS] = dict(
                        entry.options[CONF_CAMERA_DEFAULTS]
                    )
                if remote_url and remote_token:
                    options[CONF_REMOTE_HOME_ASSISTANT_URL] = remote_url
                    options[CONF_REMOTE_ACCESS_TOKEN] = remote_token

                if not await async_sync_remote_setup_values(
                    hass,
                    entry,
                    remote_url,
                    remote_token,
                ):
                    errors["base"] = "cannot_connect"
                    current_url = raw_remote_url or suggested_url
                    current_token = remote_token
                else:
                    return self.async_create_entry(title="", data=options)

            current_url = raw_remote_url or suggested_url
            current_token = remote_token
            if default_stream_type in STREAM_TYPES:
                current_stream_type = default_stream_type
            if default_position in NOTIFICATION_POSITIONS:
                current_position = default_position
            if default_duration is not None:
                current_duration = default_duration
            if default_width is not None:
                current_width = default_width
            if default_height is not None:
                current_height = default_height
            current_snapshot_fallback = default_snapshot_fallback
            current_prefer_remote_transport = prefer_remote_transport

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_STREAM_TYPE,
                        default=current_stream_type,
                    ): _select_dropdown(STREAM_TYPES),
                    vol.Optional(
                        CONF_DEFAULT_DURATION_SECONDS,
                        default=current_duration,
                    ): int,
                    vol.Optional(
                        CONF_DEFAULT_POSITION,
                        default=current_position,
                    ): _select_dropdown(NOTIFICATION_POSITIONS),
                    vol.Optional(
                        CONF_DEFAULT_SNAPSHOT_FALLBACK,
                        default=current_snapshot_fallback,
                    ): bool,
                    vol.Optional(
                        CONF_DEFAULT_WIDTH,
                        default=current_width,
                    ): int,
                    vol.Optional(
                        CONF_DEFAULT_HEIGHT,
                        default=current_height,
                    ): int,
                    vol.Optional(
                        CONF_PREFER_REMOTE_TRANSPORT,
                        default=current_prefer_remote_transport,
                    ): bool,
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


def _select_dropdown(options: tuple[str, ...]) -> Any:
    """Return a Home Assistant serializable dropdown selector for options flows."""

    if ha_selector is None:
        return vol.Any(*options)
    return ha_selector.SelectSelector(
        ha_selector.SelectSelectorConfig(
            options=list(options),
            mode=ha_selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _optional_default_int(
    value: Any,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    """Return a stored numeric default, using 0 to mean no receiver default."""

    try:
        parsed_value = int(value or 0)
    except (TypeError, ValueError):
        return None
    if not minimum <= parsed_value <= maximum:
        return None
    return parsed_value


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


def _receiver_discovery_updates(receiver: ReceiverDiscovery) -> dict[str, Any]:
    """Return mutable config-entry fields refreshed by Zeroconf discovery.

    Home Assistant calls `_abort_if_unique_id_configured` for already configured
    receivers. Passing these updates repairs DHCP address changes by stable
    receiver id without requiring the user to delete and re-add the device.
    """

    return {
        CONF_HOST: receiver.host,
        CONF_PORT: receiver.port,
        CONF_NAME: receiver.name,
        CONF_VERSION: receiver.version,
        CONF_PAIRING: receiver.pairing,
        CONF_API_VERSION: receiver.api_version,
    }


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
