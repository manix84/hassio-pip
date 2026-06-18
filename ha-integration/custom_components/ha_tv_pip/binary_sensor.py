"""Binary sensor platform for HA TV PiP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import ReceiverClientError, async_get_receiver_status
from .const import DOMAIN
from .entity import ReceiverEntity
from .services import CAMERA_COMPATIBILITY_KEY

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
            ReceiverCameraRestreamingRecommendedBinarySensor(hass, entry),
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


class ReceiverCameraRestreamingRecommendedBinarySensor(
    ReceiverEntity,
    BinarySensorEntity,
):
    """Reports whether the latest camera compatibility test recommends restreaming."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(
            entry,
            key="camera_restreaming_recommended",
            name="Camera Restreaming Recommended",
        )
        self.hass = hass
        self._attr_is_on = False
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Read the latest stored camera compatibility result."""

        result = _latest_camera_compatibility_result(self.hass, self.entry.entry_id)
        self._attr_is_on = bool(result.get("restreaming_recommended", False))
        self._attr_extra_state_attributes = {
            key: value
            for key, value in {
                "camera_entity": result.get("camera_entity"),
                "recommended_stream_type": result.get("recommended_stream_type"),
                "recommendation_reason": result.get("recommendation_reason"),
                "restreaming_reason": result.get("restreaming_reason"),
                "restreaming_next_step": result.get("restreaming_next_step"),
                "restreaming_options": result.get("restreaming_options"),
                "tested_at": result.get("tested_at"),
            }.items()
            if value is not None
        }


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

    latest: dict[str, Any] | None = None
    latest_at: str = ""
    for result in receiver_results.values():
        if not isinstance(result, dict):
            continue
        tested_at = str(result.get("tested_at", ""))
        if latest is None or tested_at > latest_at:
            latest = result
            latest_at = tested_at
    return dict(latest or {})
