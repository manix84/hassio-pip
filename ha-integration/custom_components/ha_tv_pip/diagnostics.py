"""Diagnostics support for HA TV PiP."""

from __future__ import annotations

from typing import Any

from .client import ReceiverClientError, async_get_receiver_status
from .const import CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN
from .services import CAMERA_COMPATIBILITY_KEY

REDACTED = "**REDACTED**"
REDACTED_KEYS = {
    "accessToken",
    "fallbackUrl",
    "homeAssistantUrl",
    "previewUrl",
    "token",
    "url",
}


async def async_get_config_entry_diagnostics(hass: Any, entry: Any) -> dict[str, Any]:
    """Return diagnostics for a HA TV PiP config entry."""

    data = dict(entry.data)
    if CONF_TOKEN in data:
        data[CONF_TOKEN] = REDACTED

    diagnostics: dict[str, Any] = {
        "entry": data,
        "camera_compatibility": _redact(
            getattr(hass, "data", {})
            .get(DOMAIN, {})
            .get(CAMERA_COMPATIBILITY_KEY, {})
            .get(entry.entry_id, {})
        ),
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

    receiver_status = _redact(status.raw)
    diagnostics["receiver_status"] = receiver_status
    diagnostics["compatibility"] = {
        "state": status.compatibility.state,
        "compatible": status.compatibility.compatible,
        "missing_features": list(status.compatibility.missing_features),
        "warnings": list(status.compatibility.warnings),
    }
    return diagnostics


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if key in REDACTED_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
