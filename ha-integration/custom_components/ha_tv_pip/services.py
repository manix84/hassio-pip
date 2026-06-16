"""Home Assistant services for HA TV PiP."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode, urljoin, urlparse

from .client import ReceiverClientError, ShowCameraCommand, async_show_camera
from .const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
    DOMAIN,
    SERVICE_SHOW_CAMERA,
    SERVICE_SHOW_SNAPSHOT,
)

if TYPE_CHECKING:

    class HomeAssistantError(Exception):
        """Type-checking stand-in for Home Assistant's native error."""


else:
    try:
        from homeassistant.exceptions import HomeAssistantError
    except ModuleNotFoundError:

        class HomeAssistantError(Exception):  # type: ignore[no-redef]
            """Fallback used by lightweight unit tests outside Home Assistant."""


_LOGGER = logging.getLogger(__name__)

ATTR_CAMERA_ENTITY = "camera_entity"
ATTR_DEVICE_ID = "device_id"
ATTR_DURATION_SECONDS = "duration_seconds"
ATTR_ENTER_PIP = "enter_pip"
ATTR_RECEIVER_DEVICE_ID = "receiver_device_id"
ATTR_SNAPSHOT_CAMERA_ENTITY = "snapshot_camera_entity"
ATTR_SNAPSHOT_FALLBACK = "snapshot_fallback"
ATTR_STREAM_TYPE = "stream_type"
ATTR_TITLE = "title"
CAMERA_DOMAIN = "camera"
STREAM_TYPE_AUTO = "auto"
STREAM_TYPE_HLS = "hls"
STREAM_TYPE_SNAPSHOT = "snapshot"
STREAM_TYPES = (STREAM_TYPE_AUTO, STREAM_TYPE_HLS, STREAM_TYPE_SNAPSHOT)
ERROR_MESSAGES = {
    "camera_not_found": "Camera entity was not found.",
    "camera_stream_unavailable": (
        "Home Assistant could not create an HLS stream for the camera."
    ),
    "invalid_camera_entity": "The selected entity is not a camera.",
    "invalid_duration": "Duration must be at least 1 second.",
    "invalid_stream_type": "Stream type must be auto, hls, or snapshot.",
    "missing_camera_entity": "A camera entity is required.",
    "multiple_receivers": (
        "Multiple HA TV PiP receivers are configured. Target one receiver device."
    ),
    "receiver_command_failed": (
        "The receiver rejected or could not process the camera command."
    ),
    "receiver_not_found": "No matching HA TV PiP receiver was found.",
    "receiver_not_paired": "The selected HA TV PiP receiver is not paired.",
    "snapshot_unavailable": (
        "Home Assistant could not create a snapshot URL for the camera."
    ),
}


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
    snapshot_camera_entity: str | None
    snapshot_fallback: bool
    stream_type: str
    title: str | None
    device_ids: tuple[str, ...]


class ServiceValidationError(HomeAssistantError):
    """Raised when a service call cannot be mapped to a receiver command."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = code
        self.detail = detail
        message = ERROR_MESSAGES.get(code, code)
        if detail:
            message = f"{message} Detail: {detail}"
        super().__init__(message)


async def async_register_services(hass: Any) -> None:
    """Register HA TV PiP services once per Home Assistant instance."""

    vol = __import__("voluptuous")
    cv = __import__(
        "homeassistant.helpers.config_validation",
        fromlist=["entity_id"],
    )

    base_schema = {
        vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
        vol.Optional(ATTR_DEVICE_ID): vol.Any(str, [str]),
        vol.Optional(ATTR_RECEIVER_DEVICE_ID): vol.Any(str, [str]),
        vol.Optional(ATTR_ENTER_PIP, default=True): bool,
        vol.Optional(ATTR_TITLE): str,
    }

    camera_schema = vol.Schema(
        {
            **base_schema,
            vol.Optional(ATTR_SNAPSHOT_CAMERA_ENTITY): cv.entity_id,
            vol.Optional(ATTR_SNAPSHOT_FALLBACK, default=True): bool,
            vol.Optional(ATTR_STREAM_TYPE, default=STREAM_TYPE_AUTO): vol.Any(
                *STREAM_TYPES
            ),
            vol.Optional(ATTR_DURATION_SECONDS, default=30): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
        }
    )
    snapshot_schema = vol.Schema(
        {
            **base_schema,
            vol.Optional(ATTR_DURATION_SECONDS, default=10): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
        }
    )

    async def handle_show_camera(call: Any) -> None:
        await async_handle_show_camera(hass, call)

    async def handle_show_snapshot(call: Any) -> None:
        await async_handle_show_snapshot(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW_CAMERA):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SHOW_CAMERA,
            handle_show_camera,
            schema=camera_schema,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW_SNAPSHOT):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SHOW_SNAPSHOT,
            handle_show_snapshot,
            schema=snapshot_schema,
        )


async def async_handle_show_camera(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_camera` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    title = request.title or _camera_title(hass, request.camera_entity)
    command = await _async_show_camera_command(hass, request, title=title)
    _LOGGER.info(
        "Sending camera %s to receiver %s at %s:%s using %s",
        request.camera_entity,
        receiver.name,
        receiver.host,
        receiver.port,
        command.stream_type,
    )

    try:
        await async_show_camera(
            receiver.host,
            receiver.port,
            token=receiver.token,
            command=command,
        )
    except ReceiverClientError as error:
        _LOGGER.error("Unable to send camera stream to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


async def async_handle_show_snapshot(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_snapshot` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    snapshot_url = _camera_snapshot_url(hass, request.camera_entity)
    title = request.title or _camera_title(hass, request.camera_entity)
    _LOGGER.info(
        "Sending snapshot %s to receiver %s at %s:%s",
        request.camera_entity,
        receiver.name,
        receiver.host,
        receiver.port,
    )

    try:
        await async_show_camera(
            receiver.host,
            receiver.port,
            token=receiver.token,
            command=ShowCameraCommand(
                title=title,
                url=snapshot_url,
                duration_seconds=request.duration_seconds,
                enter_pip=request.enter_pip,
                stream_type=STREAM_TYPE_SNAPSHOT,
            ),
        )
    except ReceiverClientError as error:
        _LOGGER.error("Unable to send camera snapshot to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


def _request_from_call(call: Any) -> ShowCameraRequest:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    device_ids = _tuple_value(
        data.get(ATTR_RECEIVER_DEVICE_ID)
        or data.get(ATTR_DEVICE_ID)
        or target.get(ATTR_DEVICE_ID)
    )

    duration_value = data.get(ATTR_DURATION_SECONDS, 30)
    duration_seconds = int(duration_value) if duration_value is not None else None
    if duration_seconds is not None and duration_seconds < 1:
        raise ServiceValidationError("invalid_duration")

    camera_entity = str(data.get(ATTR_CAMERA_ENTITY, "")).strip()
    if not camera_entity:
        raise ServiceValidationError("missing_camera_entity")

    stream_type = str(data.get(ATTR_STREAM_TYPE, STREAM_TYPE_AUTO)).strip().lower()
    if stream_type not in STREAM_TYPES:
        raise ServiceValidationError("invalid_stream_type")

    return ShowCameraRequest(
        camera_entity=camera_entity,
        duration_seconds=duration_seconds,
        enter_pip=bool(data.get(ATTR_ENTER_PIP, True)),
        title=_optional_text(data.get(ATTR_TITLE)),
        snapshot_camera_entity=_optional_text(data.get(ATTR_SNAPSHOT_CAMERA_ENTITY)),
        snapshot_fallback=bool(data.get(ATTR_SNAPSHOT_FALLBACK, True)),
        stream_type=stream_type,
        device_ids=device_ids,
    )


def _resolve_receiver(hass: Any, request: ShowCameraRequest) -> ReceiverEntry:
    entries = _configured_entries(hass)
    if request.device_ids:
        entries = _entries_for_devices(hass, entries, request.device_ids)

    if not entries:
        _LOGGER.warning(
            "No receiver matched service target devices: %s",
            request.device_ids,
        )
        raise ServiceValidationError("receiver_not_found")

    if len(entries) > 1:
        _LOGGER.warning(
            "Service call matched multiple receivers; target a specific receiver device"
        )
        raise ServiceValidationError("multiple_receivers")

    entry = entries[0]
    data = entry.data
    token = str(data.get(CONF_TOKEN, "")).strip()
    if not token:
        _LOGGER.warning("Receiver %s is missing a pairing token", entry.entry_id)
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
        _LOGGER.warning("Camera entity %s was not found", entity_id)
        raise ServiceValidationError("camera_not_found")


async def _async_show_camera_command(
    hass: Any,
    request: ShowCameraRequest,
    *,
    title: str,
) -> ShowCameraCommand:
    if request.stream_type == STREAM_TYPE_SNAPSHOT:
        return ShowCameraCommand(
            title=title,
            url=_camera_snapshot_url(hass, request.camera_entity),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_SNAPSHOT,
        )

    preview_url = _snapshot_preview_url(hass, request)
    try:
        return ShowCameraCommand(
            title=title,
            url=await _async_camera_stream_url(hass, request.camera_entity),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_HLS,
            preview_url=preview_url,
        )
    except ServiceValidationError as error:
        if (
            request.stream_type == STREAM_TYPE_HLS
            or error.code != "camera_stream_unavailable"
        ):
            raise

        _LOGGER.warning(
            "Falling back to snapshot for %s because HLS stream resolution failed: %s",
            request.camera_entity,
            error,
        )
        return ShowCameraCommand(
            title=title,
            url=_camera_snapshot_url(hass, request.camera_entity),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_SNAPSHOT,
        )


def _snapshot_preview_url(hass: Any, request: ShowCameraRequest) -> str | None:
    if request.stream_type == STREAM_TYPE_SNAPSHOT or not request.snapshot_fallback:
        return None

    preview_entity = request.snapshot_camera_entity or request.camera_entity
    _validate_camera_entity(hass, preview_entity)
    return _optional_camera_snapshot_url(hass, preview_entity)


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

    if not stream_url:
        _LOGGER.error("Camera stream API returned no stream URL for %s", entity_id)
        raise ServiceValidationError("camera_stream_unavailable")

    absolute_url = _absolute_stream_url(hass, str(stream_url))
    _LOGGER.debug("Resolved stream URL for %s to %s", entity_id, absolute_url)
    return absolute_url


def _absolute_stream_url(hass: Any, stream_url: str) -> str:
    parsed = urlparse(stream_url)
    if parsed.scheme and parsed.netloc:
        return stream_url

    network_module = __import__(
        "homeassistant.helpers.network",
        fromlist=["get_url"],
    )
    try:
        base_url = network_module.get_url(hass, prefer_external=False)
    except TypeError:
        base_url = network_module.get_url(hass)

    return urljoin(f"{base_url.rstrip('/')}/", stream_url.lstrip("/"))


def _camera_title(hass: Any, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    friendly_name = state.attributes.get("friendly_name") if state is not None else None
    return str(friendly_name or entity_id)


def _camera_snapshot_url(hass: Any, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    access_token = None if state is None else state.attributes.get("access_token")
    if not access_token:
        _LOGGER.error(
            "Camera entity %s does not expose a snapshot access token",
            entity_id,
        )
        raise ServiceValidationError("snapshot_unavailable")

    path = f"/api/camera_proxy/{quote(entity_id, safe='')}"
    query = urlencode({"token": str(access_token)})
    return _absolute_stream_url(hass, f"{path}?{query}")


def _optional_camera_snapshot_url(hass: Any, entity_id: str) -> str | None:
    try:
        return _camera_snapshot_url(hass, entity_id)
    except ServiceValidationError as error:
        _LOGGER.warning(
            "Snapshot fallback unavailable for %s: %s",
            entity_id,
            error,
        )
        return None


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
