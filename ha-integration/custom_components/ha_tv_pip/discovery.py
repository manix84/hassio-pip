"""Discovery helpers for HA TV PiP receivers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import DEFAULT_PORT


@dataclass(frozen=True)
class ReceiverDiscovery:
    """A receiver discovered through Zeroconf."""

    device_id: str
    name: str
    host: str
    port: int
    version: str
    pairing: str
    api_version: int


def parse_discovery_properties(
    *,
    host: str,
    port: int | None,
    properties: dict[str, Any],
) -> ReceiverDiscovery:
    """Parse Android receiver mDNS TXT records into typed discovery data."""

    device_id = _required_text(properties, "id")
    name = _text(properties.get("name"), default="HA TV PiP Receiver")
    version = _text(properties.get("version"), default="unknown")
    pairing = _text(properties.get("pairing"), default="disabled")
    api_version = _int(properties.get("api"), default=1)

    return ReceiverDiscovery(
        device_id=device_id,
        name=name,
        host=host,
        port=port or DEFAULT_PORT,
        version=version,
        pairing=pairing,
        api_version=api_version,
    )


def _required_text(properties: dict[str, Any], key: str) -> str:
    value = _text(properties.get(key), default="")
    if not value:
        raise ValueError(f"Missing required discovery property: {key}")
    return value


def _text(value: Any, *, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
