"""Sensor platform for HA TV PiP."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from .client import ReceiverClientError, ReceiverStatus, async_get_receiver_status
from .entity import ReceiverEntity

if TYPE_CHECKING:

    class SensorEntity:
        """Fallback base for unit tests outside Home Assistant."""


else:
    try:
        from homeassistant.components.sensor import SensorEntity
    except ModuleNotFoundError:

        class SensorEntity:
            """Fallback base for unit tests outside Home Assistant."""


async def async_setup_entry(hass: Any, entry: Any, async_add_entities: Any) -> None:
    """Set up HA TV PiP receiver sensors."""

    async_add_entities(
        [
            ReceiverStatusSensor(entry),
            ReceiverDisplayModeSensor(entry),
            ReceiverStreamTypeSensor(entry),
            ReceiverLastErrorSensor(entry),
            ReceiverVersionSensor(entry),
        ]
    )


class ReceiverPollingSensor(ReceiverEntity, SensorEntity):
    """Base sensor that polls the receiver status endpoint."""

    unavailable_value = "unavailable"

    def __init__(self, entry: Any, *, key: str, name: str) -> None:
        super().__init__(entry, key=key, name=name)
        self._attr_native_value: str | None = self.unavailable_value
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Poll the receiver status endpoint."""

        try:
            status = await async_get_receiver_status(self.host, self.port)
        except ReceiverClientError as error:
            self._attr_native_value = "unavailable"
            self._attr_extra_state_attributes = {
                "connected": False,
                "last_error": str(error),
                "last_seen": None,
            }
            return

        self._attr_native_value = self._native_value(status)
        self._attr_extra_state_attributes = self._extra_attributes(status)

    def _native_value(self, status: ReceiverStatus) -> str | None:
        raise NotImplementedError

    def _extra_attributes(self, status: ReceiverStatus) -> dict[str, Any]:
        return _status_attributes(status)


class ReceiverStatusSensor(ReceiverPollingSensor):
    """Receiver playback/status sensor."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="status", name="Status")

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.playback_state


class ReceiverDisplayModeSensor(ReceiverPollingSensor):
    """Receiver display mode sensor."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="display_mode", name="Active Display Mode")

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.display_mode


class ReceiverStreamTypeSensor(ReceiverPollingSensor):
    """Receiver active stream type sensor."""

    unavailable_value = "unknown"

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="stream_type", name="Active Stream Type")

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.stream_type or "unknown"


class ReceiverLastErrorSensor(ReceiverPollingSensor):
    """Receiver last error sensor."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="last_error", name="Last Receiver Error")

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.error or "none"


class ReceiverVersionSensor(ReceiverPollingSensor):
    """Receiver app version sensor."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="receiver_version", name="Receiver Version")

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.version or "unknown"


def _status_attributes(status: ReceiverStatus) -> dict[str, Any]:
    attributes = {
        "connected": True,
        "app_version": status.version,
        "api_version": status.api_version,
        "device_id": status.device_id,
        "device_name": status.device_name,
        "display_mode": status.display_mode,
        "stream_type": status.stream_type,
        "pairing_state": status.pairing_state,
        "remote_status": status.remote_status,
        "control_running": status.control_running,
        "last_request": status.last_request,
        "last_error": status.error,
        "last_seen": datetime.now().isoformat(timespec="seconds"),
    }
    capabilities = status.capabilities
    if capabilities is not None:
        attributes.update(
            {
                "capabilities_version": capabilities.capabilities_version,
                "supported_stream_types": list(capabilities.stream_types),
                "supported_positions": list(capabilities.positions),
                "supports_preview_image": capabilities.preview_image,
                "supports_playable_fallback": capabilities.playable_fallback,
                "supports_native_picture_in_picture": (
                    capabilities.native_picture_in_picture
                ),
                "supports_overlay_fallback": capabilities.overlay_fallback,
                "supports_styled_notifications": capabilities.styled_notifications,
                "supports_media_with_notification_text": (
                    capabilities.media_with_notification_text
                ),
                "supports_launcher_management": capabilities.launcher_management,
                "supports_local_pairing": capabilities.local_pairing,
                "supports_remote_receiver_settings": (
                    capabilities.remote_receiver_settings
                ),
            }
        )

    return attributes
