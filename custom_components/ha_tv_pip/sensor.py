"""Sensor platform for HA TV PiP."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from .client import ReceiverClientError, ReceiverStatus, async_get_receiver_status
from .const import DOMAIN
from .entity import ReceiverEntity
from .restreaming import RESTREAMING_PROVIDER_STATUS, restreaming_provider_metadata
from .services import (
    CAMERA_COMPATIBILITY_KEY,
    CAMERA_LAST_RESULT_KEY,
    LAST_COMMAND_RESULT_KEY,
    LAST_COMMAND_RESULT_LISTENERS_KEY,
    last_command_result_signal,
)

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
            ReceiverCompatibilitySensor(entry),
            ReceiverLastCommandResultSensor(hass, entry),
            ReceiverLastCameraCompatibilitySensor(hass, entry),
            ReceiverLastCameraResultSensor(hass, entry),
            ReceiverRestreamingProviderStatusSensor(entry),
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


class ReceiverCompatibilitySensor(ReceiverPollingSensor):
    """Receiver compatibility summary sensor."""

    def __init__(self, entry: Any) -> None:
        super().__init__(
            entry,
            key="receiver_compatibility",
            name="Receiver Compatibility",
        )

    def _native_value(self, status: ReceiverStatus) -> str:
        return status.compatibility.state

    def _extra_attributes(self, status: ReceiverStatus) -> dict[str, Any]:
        attributes = _status_attributes(status)
        attributes["summary"] = _compatibility_summary(status)
        return attributes


class ReceiverLastCameraResultSensor(ReceiverEntity, SensorEntity):
    """Last camera command result stored by the Home Assistant integration."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="last_camera_result", name="Last Camera Result")
        self.hass = hass
        self._attr_native_value: str = "none"
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Refresh the last stored camera action result."""

        result = (
            getattr(self.hass, "data", {})
            .get(DOMAIN, {})
            .get(CAMERA_LAST_RESULT_KEY, {})
            .get(self.entry.entry_id, {})
        )
        if not isinstance(result, dict) or not result:
            self._attr_native_value = "none"
            self._attr_extra_state_attributes = {}
            return

        self._attr_native_value = str(result.get("status", "unknown"))
        self._attr_extra_state_attributes = dict(result)


class ReceiverLastCommandResultSensor(ReceiverEntity, SensorEntity):
    """Last receiver command result stored by the Home Assistant integration."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="last_command_result", name="Last Command Result")
        self.hass = hass
        self._attr_native_value: str = "none"
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        """Subscribe to immediate command result updates."""

        data = self.hass.data.setdefault(DOMAIN, {})
        listeners = data.setdefault(LAST_COMMAND_RESULT_LISTENERS_KEY, {})
        entry_listeners = listeners.setdefault(self.entry.entry_id, [])
        entry_listeners.append(self._handle_command_result)

        async_on_remove = getattr(self, "async_on_remove", None)
        if callable(async_on_remove):
            async_on_remove(self._remove_direct_listener)

        try:
            dispatcher = __import__(
                "homeassistant.helpers.dispatcher",
                fromlist=["async_dispatcher_connect"],
            )
        except ModuleNotFoundError:
            return

        remove_listener = dispatcher.async_dispatcher_connect(
            self.hass,
            last_command_result_signal(self.entry.entry_id),
            self._handle_command_result,
        )
        async_on_remove = getattr(self, "async_on_remove", None)
        if callable(async_on_remove):
            async_on_remove(remove_listener)

    def _remove_direct_listener(self) -> None:
        listeners = (
            getattr(self.hass, "data", {})
            .get(DOMAIN, {})
            .get(LAST_COMMAND_RESULT_LISTENERS_KEY, {})
            .get(self.entry.entry_id, [])
        )
        if self._handle_command_result in listeners:
            listeners.remove(self._handle_command_result)

    async def async_update(self) -> None:
        """Refresh the last stored receiver command result."""

        self._refresh_from_hass_data()

    def _handle_command_result(self) -> None:
        """Refresh state after a command result is stored."""

        self._refresh_from_hass_data()
        async_write_ha_state = getattr(self, "async_write_ha_state", None)
        if callable(async_write_ha_state):
            async_write_ha_state()

    def _refresh_from_hass_data(self) -> None:
        result = (
            getattr(self.hass, "data", {})
            .get(DOMAIN, {})
            .get(LAST_COMMAND_RESULT_KEY, {})
            .get(self.entry.entry_id, {})
        )
        if not isinstance(result, dict) or not result:
            self._attr_native_value = "none"
            self._attr_extra_state_attributes = {}
            return

        command_type = str(result.get("command_type", "unknown"))
        status = str(result.get("status", "unknown"))
        self._attr_native_value = f"{command_type}:{status}"
        self._attr_extra_state_attributes = dict(result)


class ReceiverLastCameraCompatibilitySensor(ReceiverEntity, SensorEntity):
    """Latest camera compatibility test result stored by the integration."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(
            entry,
            key="last_camera_compatibility",
            name="Last Camera Compatibility",
        )
        self.hass = hass
        self._attr_native_value: str = "none"
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Refresh the last stored camera compatibility result."""

        result = _latest_camera_compatibility_result(self.hass, self.entry.entry_id)
        if not result:
            self._attr_native_value = "none"
            self._attr_extra_state_attributes = {}
            return

        self._attr_native_value = str(result.get("recommended_stream_type", "none"))
        self._attr_extra_state_attributes = result


class ReceiverRestreamingProviderStatusSensor(ReceiverEntity, SensorEntity):
    """Current restreaming provider availability for this integration."""

    def __init__(self, entry: Any) -> None:
        super().__init__(
            entry,
            key="restreaming_provider_status",
            name="Restreaming Provider Status",
        )
        self._attr_native_value = RESTREAMING_PROVIDER_STATUS
        self._attr_extra_state_attributes = restreaming_provider_metadata()


def _latest_camera_compatibility_result(
    hass: Any,
    entry_id: str,
) -> dict[str, Any]:
    receiver_results = (
        getattr(hass, "data", {})
        .get(DOMAIN, {})
        .get(CAMERA_COMPATIBILITY_KEY, {})
        .get(entry_id, {})
    )
    if not isinstance(receiver_results, dict):
        return {}

    results: list[dict[str, Any]] = []
    for result in receiver_results.values():
        if isinstance(result, dict):
            results.append(dict(result))

    if not results:
        return {}

    latest = results[0]
    for result in results[1:]:
        if str(result.get("tested_at", "")) > str(latest.get("tested_at", "")):
            latest = result
    return latest


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
        "compatibility_state": status.compatibility.state,
        "compatible": status.compatibility.compatible,
        "missing_features": list(status.compatibility.missing_features),
        "compatibility_warnings": list(status.compatibility.warnings),
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


def _compatibility_summary(status: ReceiverStatus) -> str:
    state = status.compatibility.state
    if state == "compatible":
        return "Receiver supports the current integration feature set."
    if state == "degraded":
        return (
            "Receiver is usable, but some optional features are unavailable. "
            "Update the Android receiver app when practical."
        )
    if state == "legacy":
        return (
            "Receiver is usable, but does not report detailed capabilities. "
            "Update the Android receiver app for safer automatic feature handling."
        )
    if state == "incompatible":
        return (
            "Receiver is missing required API or display capabilities. "
            "Update the Android receiver app before sending camera commands."
        )
    return "Receiver compatibility state is unknown."
