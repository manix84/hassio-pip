"""Diagnostics support for HA TV PiP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import ReceiverClientError, async_get_receiver_status
from .const import CONF_CAMERA_DEFAULTS, CONF_HOST, CONF_PORT, CONF_TOKEN, DOMAIN
from .restreaming import restreaming_provider_metadata
from .services import (
    CAMERA_COMPATIBILITY_KEY,
    CAMERA_LAST_RESULT_KEY,
    LAST_COMMAND_RESULT_KEY,
)

REDACTED = "**REDACTED**"
REDACTED_KEYS = {
    "accessToken",
    "fallbackUrl",
    "homeAssistantUrl",
    "previewUrl",
    "restream_url",
    "restreamUrl",
    "token",
    "url",
}
MIN_HACS_OPTIONS_FLOW_VERSION = "1.27.9"


async def async_get_config_entry_diagnostics(hass: Any, entry: Any) -> dict[str, Any]:
    """Return diagnostics for a HA TV PiP config entry."""

    data = dict(entry.data)
    if CONF_TOKEN in data:
        data[CONF_TOKEN] = REDACTED

    diagnostics: dict[str, Any] = {
        "entry": data,
        "integration": {
            "version": _manifest_version(),
            "minimum_hacs_options_flow_version": MIN_HACS_OPTIONS_FLOW_VERSION,
        },
        "camera_defaults": _redact(
            dict(getattr(entry, "options", {}) or {}).get(CONF_CAMERA_DEFAULTS, {})
        ),
        "camera_compatibility": _redact(
            getattr(hass, "data", {})
            .get(DOMAIN, {})
            .get(CAMERA_COMPATIBILITY_KEY, {})
            .get(entry.entry_id, {})
        ),
        "camera_last_result": _redact(
            getattr(hass, "data", {})
            .get(DOMAIN, {})
            .get(CAMERA_LAST_RESULT_KEY, {})
            .get(entry.entry_id, {})
        ),
        "last_command_result": _redact(
            getattr(hass, "data", {})
            .get(DOMAIN, {})
            .get(LAST_COMMAND_RESULT_KEY, {})
            .get(entry.entry_id, {})
        ),
        "restreaming_providers": restreaming_provider_metadata(),
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


def _manifest_version() -> str:
    manifest_path = Path(__file__).with_name("manifest.json")
    try:
        with manifest_path.open(encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(manifest.get("version", "unknown"))


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if key in REDACTED_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
