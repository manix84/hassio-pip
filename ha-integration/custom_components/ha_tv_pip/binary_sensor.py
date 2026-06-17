"""Binary sensor platform for HA TV PiP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import ReceiverClientError, async_get_receiver_status
from .entity import ReceiverEntity

if TYPE_CHECKING:

    class BinarySensorEntity:
        """Fallback base for unit tests outside Home Assistant."""


else:
    try:
        from homeassistant.components.binary_sensor import BinarySensorEntity
    except ModuleNotFoundError:

        class BinarySensorEntity:
            """Fallback base for unit tests outside Home Assistant."""


async def async_setup_entry(hass: Any, entry: Any, async_add_entities: Any) -> None:
    """Set up HA TV PiP receiver binary sensors."""

    async_add_entities(
        [
            ReceiverConnectedBinarySensor(entry),
            ReceiverRemoteConnectedBinarySensor(entry),
        ]
    )


class ReceiverPollingBinarySensor(ReceiverEntity, BinarySensorEntity):
    """Base binary sensor that polls the receiver status endpoint."""

    def __init__(self, entry: Any, *, key: str, name: str) -> None:
        super().__init__(entry, key=key, name=name)
        self._attr_is_on = False
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Poll the receiver status endpoint."""

        try:
            status = await async_get_receiver_status(self.host, self.port)
        except ReceiverClientError as error:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {"last_error": str(error)}
            return

        self._attr_is_on = self._is_on_from_status(status)
        self._attr_extra_state_attributes = self._extra_attributes(status)

    def _is_on_from_status(self, status: Any) -> bool:
        raise NotImplementedError

    def _extra_attributes(self, status: Any) -> dict[str, Any]:
        return {
            "control_running": status.control_running,
            "app_version": status.version,
            "api_version": status.api_version,
        }


class ReceiverConnectedBinarySensor(ReceiverPollingBinarySensor):
    """Reports whether the receiver status endpoint is reachable."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="connected", name="Connected")

    def _is_on_from_status(self, status: Any) -> bool:
        return True


class ReceiverRemoteConnectedBinarySensor(ReceiverPollingBinarySensor):
    """Reports whether the receiver is connected through remote receiver mode."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="remote_connected", name="Remote Connected")

    def _is_on_from_status(self, status: Any) -> bool:
        return bool(status.remote_status == "connected")

    def _extra_attributes(self, status: Any) -> dict[str, Any]:
        attributes = super()._extra_attributes(status)
        attributes["remote_status"] = status.remote_status
        return attributes
