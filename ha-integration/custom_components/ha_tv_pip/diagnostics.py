"""Diagnostics support for HA TV PiP."""

from __future__ import annotations

from typing import Any

from .client import ReceiverClientError, async_get_receiver_status
from .const import CONF_HOST, CONF_PORT, CONF_TOKEN

REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(hass: Any, entry: Any) -> dict[str, Any]:
    """Return diagnostics for a HA TV PiP config entry."""

    data = dict(entry.data)
    if CONF_TOKEN in data:
        data[CONF_TOKEN] = REDACTED

    diagnostics: dict[str, Any] = {
        "entry": data,
        "receiver_status": None,
        "receiver_error": None,
    }

    try:
        status = await async_get_receiver_status(
            str(entry.data[CONF_HOST]),
            int(entry.data[CONF_PORT]),
        )
    except (KeyError, ReceiverClientError, TypeError, ValueError) as error:
        diagnostics["receiver_error"] = str(error)
        return diagnostics

    receiver_status = dict(status.raw)
    if "url" in receiver_status:
        receiver_status["url"] = REDACTED
    diagnostics["receiver_status"] = receiver_status
    return diagnostics
