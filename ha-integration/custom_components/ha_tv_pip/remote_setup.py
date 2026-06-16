"""Helpers for provisioning remote receiver settings from Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

from .client import (
    ReceiverClientError,
    async_clear_remote_configuration,
    async_set_remote_configuration,
)
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


def suggested_remote_home_assistant_url(hass: Any) -> str:
    """Return Home Assistant's preferred external URL when configured."""

    try:
        network = __import__("homeassistant.helpers.network", fromlist=["get_url"])
    except ModuleNotFoundError:
        return ""

    try:
        return str(
            network.get_url(
                hass,
                prefer_external=True,
                allow_internal=False,
            )
        )
    except Exception:  # pragma: no cover - depends on Home Assistant runtime config
        return ""


def resolved_remote_setup(entry: Any, hass: Any) -> tuple[str, str]:
    """Return the remote URL and token that should be provisioned."""

    options = getattr(entry, "options", {})
    remote_url = str(options.get(CONF_REMOTE_HOME_ASSISTANT_URL, "")).strip()
    remote_token = str(options.get(CONF_REMOTE_ACCESS_TOKEN, "")).strip()
    if not remote_url and remote_token:
        remote_url = suggested_remote_home_assistant_url(hass)
    return remote_url, remote_token


async def async_sync_remote_setup(hass: Any, entry: Any) -> bool:
    """Push remote setup from the config entry to the paired receiver."""
    return await async_sync_remote_setup_values(
        hass,
        entry,
        *resolved_remote_setup(entry, hass),
    )


async def async_sync_remote_setup_values(
    hass: Any,
    entry: Any,
    remote_url: str,
    remote_token: str,
) -> bool:
    """Push explicit remote setup values to the paired receiver."""

    host = str(entry.data[CONF_HOST])
    port = int(entry.data[CONF_PORT])
    pairing_token = str(entry.data.get(CONF_TOKEN, "")).strip()
    if not pairing_token:
        return False

    try:
        if remote_url and remote_token:
            return await async_set_remote_configuration(
                host,
                port,
                token=pairing_token,
                home_assistant_url=remote_url,
                access_token=remote_token,
            )
        return await async_clear_remote_configuration(
            host,
            port,
            token=pairing_token,
        )
    except ReceiverClientError as error:
        _LOGGER.warning("Unable to sync HA TV PiP remote setup: %s", error)
        return False
