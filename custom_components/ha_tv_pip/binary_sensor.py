"""Binary sensor platform for HA TV PiP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import ReceiverClientError, ReceiverStatus, async_get_receiver_status
from .const import DOMAIN
from .entity import ReceiverEntity
from .remote import remote_registry
from .restreaming import restreaming_provider_metadata
from .services import (
    CAMERA_COMPATIBILITY_KEY,
    _async_get_receiver_status_command,
    _prefer_remote_transport,
    _resolve_receiver_from_entry,
)

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
            ReceiverConnectedBinarySensor(entry, hass=hass),
            ReceiverRemoteConnectedBinarySensor(entry, hass=hass),
            ReceiverCameraRestreamingRecommendedBinarySensor(hass, entry),
        ]
    )


class ReceiverPollingBinarySensor(ReceiverEntity, BinarySensorEntity):
    """Base binary sensor that polls the receiver status endpoint."""

    def __init__(
        self,
        entry: Any,
        *,
        key: str,
        name: str,
        hass: Any | None = None,
    ) -> None:
        super().__init__(entry, key=key, name=name)
        self.hass = hass
        self._attr_is_on = False
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_update(self) -> None:
        """Poll the receiver status endpoint."""

        try:
            status, transport = await _async_status_for_entry(
                self.hass,
                self.entry,
                self.host,
                self.port,
            )
        except ReceiverClientError as error:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {"last_error": str(error)}
            return

        self._attr_is_on = self._is_on_from_status(status)
        self._attr_extra_state_attributes = self._extra_attributes(status)
        self._attr_extra_state_attributes["transport"] = transport

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

    def __init__(self, entry: Any, *, hass: Any | None = None) -> None:
        super().__init__(entry, key="connected", name="Connected", hass=hass)

    def _is_on_from_status(self, status: Any) -> bool:
        return True


class ReceiverRemoteConnectedBinarySensor(ReceiverPollingBinarySensor):
    """Reports whether the receiver is connected through remote receiver mode."""

    def __init__(self, entry: Any, *, hass: Any | None = None) -> None:
        super().__init__(
            entry,
            key="remote_connected",
            name="Remote Connected",
            hass=hass,
        )

    def _is_on_from_status(self, status: Any) -> bool:
        return bool(status.remote_status == "connected")

    def _extra_attributes(self, status: Any) -> dict[str, Any]:
        attributes = super()._extra_attributes(status)
        attributes["remote_status"] = status.remote_status
        remote = status.remote
        if remote is not None:
            attributes.update(
                {
                    "remote_home_assistant_url_configured": (
                        remote.home_assistant_url is not None
                    ),
                    "remote_last_error": remote.last_error,
                    "remote_connected_at_millis": remote.connected_at_millis,
                    "remote_last_message_at_millis": remote.last_message_at_millis,
                    "remote_connection_attempt_count": (
                        remote.connection_attempt_count
                    ),
                    "remote_successful_connection_count": (
                        remote.successful_connection_count
                    ),
                    "remote_message_count": remote.message_count,
                    "remote_last_connection_attempt_at_millis": (
                        remote.last_connection_attempt_at_millis
                    ),
                    "remote_last_disconnected_at_millis": (
                        remote.last_disconnected_at_millis
                    ),
                    "remote_last_disconnect_reason": remote.last_disconnect_reason,
                }
            )
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
        if not result:
            self._attr_extra_state_attributes = {}
            return

        provider_metadata = restreaming_provider_metadata()
        self._attr_extra_state_attributes = {
            key: value
            for key, value in {
                "camera_entity": result.get("camera_entity"),
                "recommended_stream_type": result.get("recommended_stream_type"),
                "recommendation_reason": result.get("recommendation_reason"),
                "restreaming_reason": result.get("restreaming_reason"),
                "restreaming_next_step": result.get("restreaming_next_step"),
                "restreaming_options": result.get("restreaming_options"),
                "restreaming_provider_status": provider_metadata.get("status"),
                "restreaming_supported_providers": provider_metadata.get(
                    "supported_providers"
                ),
                "restreaming_planned_providers": provider_metadata.get(
                    "planned_providers"
                ),
                "restreaming_recommended_current_paths": provider_metadata.get(
                    "recommended_current_paths"
                ),
                "restreaming_documentation_url": provider_metadata.get(
                    "documentation_url"
                ),
                "tested_at": result.get("tested_at"),
            }.items()
            if value is not None
        }


async def _async_status_for_entry(
    hass: Any | None,
    entry: Any,
    host: str,
    port: int,
) -> tuple[ReceiverStatus, str]:
    if hass is None:
        return await async_get_receiver_status(host, port), "local"

    receiver = _resolve_receiver_from_entry(entry)
    remote = remote_registry(hass)
    return await _async_get_receiver_status_command(
        receiver,
        remote,
        prefer_remote=_prefer_remote_transport(receiver, remote),
    )


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
