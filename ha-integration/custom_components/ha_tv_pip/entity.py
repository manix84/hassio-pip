"""Shared Home Assistant entity helpers for HA TV PiP."""

from __future__ import annotations

from typing import Any

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_NAME, CONF_PORT, DOMAIN


class ReceiverEntity:
    """Common receiver entity metadata."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: Any,
        *,
        key: str,
        name: str,
        translation_key: str | None = None,
    ) -> None:
        self.entry = entry
        self._attr_name = name
        self._attr_translation_key = translation_key or key
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data[CONF_DEVICE_ID])},
            "manufacturer": "HA TV PiP",
            "model": "Android TV Receiver",
            "name": entry.data.get(CONF_NAME, "HA TV PiP Receiver"),
        }

    @property
    def host(self) -> str:
        return str(self.entry.data[CONF_HOST])

    @property
    def port(self) -> int:
        return int(self.entry.data[CONF_PORT])
