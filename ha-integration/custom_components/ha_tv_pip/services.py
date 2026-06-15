"""Home Assistant services for HA TV PiP."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .client import ReceiverClientError, ShowCameraCommand, async_show_camera
from .const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
    DOMAIN,
    SERVICE_SHOW_CAMERA,
)

_LOGGER = logging.getLogger(__name__)

ATTR_CAMERA_ENTITY = "camera_entity"
ATTR_DEVICE_ID = "device_id"
ATTR_DURATION_SECONDS = "duration_seconds"
ATTR_ENTER_PIP = "enter_pip"
ATTR_TITLE = "title"
CAMERA_DOMAIN = "camera"


@dataclass(frozen=True)
class ReceiverEntry:
    """Minimal receiver config entry data required by services."""

    entry_id: str
    name: str
    host: str
    port: int
    token: str


@dataclass(frozen=True)
class ShowCameraRequest:
    """Validated service request."""

    camera_entity: str
    duration_seconds: int | None
    enter_pip: bool
    title: str | None
    device_ids: tuple[str, ...]


class ServiceValidationError(ValueError):
    """Raised when a service call cannot be mapped to a receiver command."""


async def async_register_services(hass: Any) -> None:
    """Register HA TV PiP services once per Home Assistant instance."""

    if hass.services.has_service(DOMAIN, SERVICE_SHOW_CAMERA):
        return

    vol = __import__("voluptuous")
    cv = __import__(
        "homeassistant.helpers.config_validation",
        fromlist=["entity_id"],
    )

    schema = vol.Schema(
        {
            vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
            vol.Optional(ATTR_DEVICE_ID): vol.Any(str, [str]),
            vol.Optional(ATTR_DURATION_SECONDS, default=30): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
            vol.Optional(ATTR_ENTER_PIP, default=True): bool,
            vol.Optional(ATTR_TITLE): str,
        }
    )

    async def handle_show_camera(call: Any) -> None:
        await async_handle_show_camera(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SHOW_CAMERA,
        handle_show_camera,
        schema=schema,
    )


async def async_handle_show_camera(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_camera` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    stream_url = await _async_camera_stream_url(hass, request.camera_entity)
    title = request.title or _camera_title(hass, request.camera_entity)

    try:
        await async_show_camera(
            receiver.host,
            receiver.port,
            token=receiver.token,
            command=ShowCameraCommand(
                title=title,
                url=stream_url,
                duration_seconds=request.duration_seconds,
                enter_pip=request.enter_pip,
            ),
        )
    except ReceiverClientError as error:
        _LOGGER.error("Unable to send camera stream to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed") from error


def _request_from_call(call: Any) -> ShowCameraRequest:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    device_ids = _tuple_value(data.get(ATTR_DEVICE_ID) or target.get(ATTR_DEVICE_ID))

    duration_value = data.get(ATTR_DURATION_SECONDS, 30)
    duration_seconds = int(duration_value) if duration_value is not None else None
    if duration_seconds is not None and duration_seconds < 1:
        raise ServiceValidationError("invalid_duration")

    camera_entity = str(data.get(ATTR_CAMERA_ENTITY, "")).strip()
    if not camera_entity:
        raise ServiceValidationError("missing_camera_entity")

    return ShowCameraRequest(
        camera_entity=camera_entity,
        duration_seconds=duration_seconds,
        enter_pip=bool(data.get(ATTR_ENTER_PIP, True)),
        title=_optional_text(data.get(ATTR_TITLE)),
        device_ids=device_ids,
    )


def _resolve_receiver(hass: Any, request: ShowCameraRequest) -> ReceiverEntry:
    entries = _configured_entries(hass)
    if request.device_ids:
        entries = _entries_for_devices(hass, entries, request.device_ids)

    if not entries:
        raise ServiceValidationError("receiver_not_found")

    if len(entries) > 1:
        raise ServiceValidationError("multiple_receivers")

    entry = entries[0]
    data = entry.data
    token = str(data.get(CONF_TOKEN, "")).strip()
    if not token:
        raise ServiceValidationError("receiver_not_paired")

    return ReceiverEntry(
        entry_id=entry.entry_id,
        name=str(data.get(CONF_NAME, "HA TV PiP Receiver")),
        host=str(data[CONF_HOST]),
        port=int(data[CONF_PORT]),
        token=token,
    )


def _configured_entries(hass: Any) -> list[Any]:
    config_entries = getattr(hass, "config_entries", None)
    if config_entries is None:
        data_entries = getattr(hass, "data", {}).get(DOMAIN, {}).get("entries", {})
        return list(data_entries.values())
    return list(config_entries.async_entries(DOMAIN))


def _entries_for_devices(
    hass: Any,
    entries: list[Any],
    device_ids: tuple[str, ...],
) -> list[Any]:
    device_registry_module = __import__(
        "homeassistant.helpers.device_registry",
        fromlist=["async_get"],
    )
    device_registry = device_registry_module.async_get(hass)
    matched_entry_ids: set[str] = set()
    for device_id in device_ids:
        device = device_registry.async_get(device_id)
        if device is None:
            continue
        matched_entry_ids.update(device.config_entries)

    return [entry for entry in entries if entry.entry_id in matched_entry_ids]


def _validate_camera_entity(hass: Any, entity_id: str) -> None:
    if not entity_id.startswith(f"{CAMERA_DOMAIN}."):
        raise ServiceValidationError("invalid_camera_entity")

    state = hass.states.get(entity_id)
    if state is None:
        raise ServiceValidationError("camera_not_found")


async def _async_camera_stream_url(hass: Any, entity_id: str) -> str:
    camera_module = __import__(
        "homeassistant.components.camera",
        fromlist=["async_request_stream"],
    )
    exceptions_module = __import__(
        "homeassistant.exceptions",
        fromlist=["HomeAssistantError"],
    )

    try:
        stream_url = await camera_module.async_request_stream(hass, entity_id, "hls")
    except exceptions_module.HomeAssistantError as error:
        _LOGGER.error("Unable to resolve stream for %s: %s", entity_id, error)
        raise ServiceValidationError("camera_stream_unavailable") from error
    return str(stream_url)


def _camera_title(hass: Any, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    friendly_name = state.attributes.get("friendly_name") if state is not None else None
    return str(friendly_name or entity_id)


def _tuple_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
