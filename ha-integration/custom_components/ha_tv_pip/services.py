"""Home Assistant services for HA TV PiP."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode, urljoin, urlparse

from .client import ReceiverClientError, ShowCameraCommand, async_show_camera
from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
    DOMAIN,
    SERVICE_SHOW_CAMERA,
    SERVICE_SHOW_NOTIFICATION,
    SERVICE_SHOW_SNAPSHOT,
)
from .remote import remote_registry

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
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_HEIGHT = "height"
ATTR_MESSAGE = "message"
ATTR_MESSAGE_COLOR = "message_color"
ATTR_MESSAGE_SIZE = "message_size"
ATTR_POSITION = "position"
ATTR_RECEIVER_DEVICE_ID = "receiver_device_id"
ATTR_SNAPSHOT_CAMERA_ENTITY = "snapshot_camera_entity"
ATTR_SNAPSHOT_FALLBACK = "snapshot_fallback"
ATTR_STREAM_TYPE = "stream_type"
ATTR_TITLE = "title"
ATTR_TITLE_COLOR = "title_color"
ATTR_TITLE_SIZE = "title_size"
ATTR_WIDTH = "width"
CAMERA_DOMAIN = "camera"
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_NOTIFICATION_BACKGROUND_COLOR = "#0f0e0e"
DEFAULT_NOTIFICATION_MESSAGE_COLOR = "#fbf5f5"
DEFAULT_NOTIFICATION_TITLE = "Home Assistant"
DEFAULT_NOTIFICATION_TITLE_COLOR = "#50BFF2"
NOTIFICATION_POSITIONS = ("top_right", "top_left", "bottom_right", "bottom_left")
STREAM_TYPE_AUTO = "auto"
STREAM_TYPE_HLS = "hls"
STREAM_TYPE_NOTIFICATION = "notification"
STREAM_TYPE_SNAPSHOT = "snapshot"
STREAM_TYPES = (STREAM_TYPE_AUTO, STREAM_TYPE_HLS, STREAM_TYPE_SNAPSHOT)
ERROR_MESSAGES = {
    "camera_not_found": "Camera entity was not found.",
    "camera_stream_unavailable": (
        "Home Assistant could not create an HLS stream for the camera."
    ),
    "invalid_camera_entity": "The selected entity is not a camera.",
    "invalid_duration": "Duration must be at least 1 second.",
    "invalid_color": "Notification colors must be six-digit hex values.",
    "invalid_notification_size": (
        "Notification text sizes are outside the supported range."
    ),
    "invalid_overlay_size": "Overlay width or height is outside the supported range.",
    "invalid_position": (
        "Notification position must be top_right, top_left, bottom_right, "
        "or bottom_left."
    ),
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
    device_id: str
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
    message: str | None
    position: str
    title_color: str
    title_size: int
    message_color: str
    message_size: int
    background_color: str
    width: int | None
    height: int | None
    snapshot_camera_entity: str | None
    snapshot_fallback: bool
    stream_type: str
    title: str | None
    device_ids: tuple[str, ...]


@dataclass(frozen=True)
class ShowNotificationRequest:
    """Validated notification service request."""

    title: str
    message: str | None
    duration_seconds: int | None
    enter_pip: bool
    position: str
    title_color: str
    title_size: int
    message_color: str
    message_size: int
    background_color: str
    width: int | None
    height: int | None
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
        vol.Optional(ATTR_MESSAGE): str,
        vol.Optional(ATTR_POSITION, default="top_right"): vol.Any(
            *NOTIFICATION_POSITIONS
        ),
        vol.Optional(
            ATTR_TITLE_COLOR,
            default=DEFAULT_NOTIFICATION_TITLE_COLOR,
        ): str,
        vol.Optional(ATTR_TITLE_SIZE, default=24): vol.All(
            vol.Coerce(int),
            vol.Range(min=10, max=48),
        ),
        vol.Optional(
            ATTR_MESSAGE_COLOR,
            default=DEFAULT_NOTIFICATION_MESSAGE_COLOR,
        ): str,
        vol.Optional(ATTR_MESSAGE_SIZE, default=18): vol.All(
            vol.Coerce(int),
            vol.Range(min=10, max=40),
        ),
        vol.Optional(
            ATTR_BACKGROUND_COLOR,
            default=DEFAULT_NOTIFICATION_BACKGROUND_COLOR,
        ): str,
        vol.Optional(ATTR_WIDTH): vol.All(
            vol.Coerce(int),
            vol.Range(min=240, max=1600),
        ),
        vol.Optional(ATTR_HEIGHT): vol.All(
            vol.Coerce(int),
            vol.Range(min=120, max=900),
        ),
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
    notification_schema = vol.Schema(
        {
            vol.Optional(ATTR_DEVICE_ID): vol.Any(str, [str]),
            vol.Optional(ATTR_RECEIVER_DEVICE_ID): vol.Any(str, [str]),
            vol.Optional(ATTR_TITLE, default=DEFAULT_NOTIFICATION_TITLE): str,
            vol.Optional(ATTR_MESSAGE): str,
            vol.Optional(ATTR_DURATION_SECONDS, default=15): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
            vol.Optional(ATTR_ENTER_PIP, default=True): bool,
            vol.Optional(ATTR_POSITION, default="top_right"): vol.Any(
                *NOTIFICATION_POSITIONS
            ),
            vol.Optional(
                ATTR_TITLE_COLOR,
                default=DEFAULT_NOTIFICATION_TITLE_COLOR,
            ): str,
            vol.Optional(ATTR_TITLE_SIZE, default=24): vol.All(
                vol.Coerce(int),
                vol.Range(min=10, max=48),
            ),
            vol.Optional(
                ATTR_MESSAGE_COLOR,
                default=DEFAULT_NOTIFICATION_MESSAGE_COLOR,
            ): str,
            vol.Optional(ATTR_MESSAGE_SIZE, default=18): vol.All(
                vol.Coerce(int),
                vol.Range(min=10, max=40),
            ),
            vol.Optional(
                ATTR_BACKGROUND_COLOR,
                default=DEFAULT_NOTIFICATION_BACKGROUND_COLOR,
            ): str,
            vol.Optional(ATTR_WIDTH): vol.All(
                vol.Coerce(int),
                vol.Range(min=240, max=1600),
            ),
            vol.Optional(ATTR_HEIGHT): vol.All(
                vol.Coerce(int),
                vol.Range(min=120, max=900),
            ),
        }
    )

    async def handle_show_camera(call: Any) -> None:
        await async_handle_show_camera(hass, call)

    async def handle_show_snapshot(call: Any) -> None:
        await async_handle_show_snapshot(hass, call)

    async def handle_show_notification(call: Any) -> None:
        await async_handle_show_notification(hass, call)

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

    if not hass.services.has_service(DOMAIN, SERVICE_SHOW_NOTIFICATION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SHOW_NOTIFICATION,
            handle_show_notification,
            schema=notification_schema,
        )


async def async_handle_show_camera(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_camera` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    title = request.title or _camera_title(hass, request.camera_entity)
    remote = remote_registry(hass)
    prefer_external = remote.is_connected(receiver.device_id)
    command = await _async_show_camera_command(
        hass,
        request,
        title=title,
        prefer_external=prefer_external,
    )
    _LOGGER.info(
        "Sending camera %s to receiver %s using %s transport and %s stream",
        request.camera_entity,
        receiver.name,
        "remote" if prefer_external else "local",
        command.stream_type,
    )

    try:
        if await remote.async_send_show(device_id=receiver.device_id, command=command):
            return
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
    remote = remote_registry(hass)
    prefer_external = remote.is_connected(receiver.device_id)
    snapshot_url = _camera_snapshot_url(
        hass,
        request.camera_entity,
        prefer_external=prefer_external,
    )
    title = request.title or _camera_title(hass, request.camera_entity)
    _LOGGER.info(
        "Sending snapshot %s to receiver %s using %s transport",
        request.camera_entity,
        receiver.name,
        "remote" if prefer_external else "local",
    )

    try:
        command = ShowCameraCommand(
            title=title,
            url=snapshot_url,
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_SNAPSHOT,
            **_presentation_payload(request),
        )
        if await remote.async_send_show(device_id=receiver.device_id, command=command):
            return
        await async_show_camera(
            receiver.host,
            receiver.port,
            token=receiver.token,
            command=command,
        )
    except ReceiverClientError as error:
        _LOGGER.error("Unable to send camera snapshot to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


async def async_handle_show_notification(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_notification` service calls."""

    request = _notification_request_from_call(call)
    receiver = _resolve_receiver(hass, request)
    remote = remote_registry(hass)
    prefer_external = remote.is_connected(receiver.device_id)
    _LOGGER.info(
        "Sending notification to receiver %s using %s transport",
        receiver.name,
        "remote" if prefer_external else "local",
    )

    try:
        command = ShowCameraCommand(
            title=request.title,
            url="",
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_NOTIFICATION,
            message=request.message,
            position=request.position,
            title_color=request.title_color,
            title_size=request.title_size,
            message_color=request.message_color,
            message_size=request.message_size,
            background_color=request.background_color,
            width=request.width,
            height=request.height,
        )
        if await remote.async_send_show(device_id=receiver.device_id, command=command):
            return
        await async_show_camera(
            receiver.host,
            receiver.port,
            token=receiver.token,
            command=command,
        )
    except ReceiverClientError as error:
        _LOGGER.error("Unable to send notification to %s: %s", receiver.name, error)
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
        message=_optional_text(data.get(ATTR_MESSAGE)),
        position=_notification_position(data),
        title_color=_validated_color(
            data.get(ATTR_TITLE_COLOR),
            DEFAULT_NOTIFICATION_TITLE_COLOR,
        ),
        title_size=_notification_size(data.get(ATTR_TITLE_SIZE, 24), 10, 48),
        message_color=_validated_color(
            data.get(ATTR_MESSAGE_COLOR),
            DEFAULT_NOTIFICATION_MESSAGE_COLOR,
        ),
        message_size=_notification_size(data.get(ATTR_MESSAGE_SIZE, 18), 10, 40),
        background_color=_validated_color(
            data.get(ATTR_BACKGROUND_COLOR),
            DEFAULT_NOTIFICATION_BACKGROUND_COLOR,
        ),
        width=_optional_overlay_dimension(data.get(ATTR_WIDTH), 240, 1600),
        height=_optional_overlay_dimension(data.get(ATTR_HEIGHT), 120, 900),
        title=_optional_text(data.get(ATTR_TITLE)),
        snapshot_camera_entity=_optional_text(data.get(ATTR_SNAPSHOT_CAMERA_ENTITY)),
        snapshot_fallback=bool(data.get(ATTR_SNAPSHOT_FALLBACK, True)),
        stream_type=stream_type,
        device_ids=device_ids,
    )


def _notification_request_from_call(call: Any) -> ShowNotificationRequest:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    device_ids = _tuple_value(
        data.get(ATTR_RECEIVER_DEVICE_ID)
        or data.get(ATTR_DEVICE_ID)
        or target.get(ATTR_DEVICE_ID)
    )
    duration_value = data.get(ATTR_DURATION_SECONDS, 15)
    duration_seconds = int(duration_value) if duration_value is not None else None
    if duration_seconds is not None and duration_seconds < 1:
        raise ServiceValidationError("invalid_duration")

    return ShowNotificationRequest(
        title=_optional_text(data.get(ATTR_TITLE)) or DEFAULT_NOTIFICATION_TITLE,
        message=_optional_text(data.get(ATTR_MESSAGE)),
        duration_seconds=duration_seconds,
        enter_pip=bool(data.get(ATTR_ENTER_PIP, True)),
        position=_notification_position(data),
        title_color=_validated_color(
            data.get(ATTR_TITLE_COLOR),
            DEFAULT_NOTIFICATION_TITLE_COLOR,
        ),
        title_size=_notification_size(data.get(ATTR_TITLE_SIZE, 24), 10, 48),
        message_color=_validated_color(
            data.get(ATTR_MESSAGE_COLOR),
            DEFAULT_NOTIFICATION_MESSAGE_COLOR,
        ),
        message_size=_notification_size(data.get(ATTR_MESSAGE_SIZE, 18), 10, 40),
        background_color=_validated_color(
            data.get(ATTR_BACKGROUND_COLOR),
            DEFAULT_NOTIFICATION_BACKGROUND_COLOR,
        ),
        width=_optional_overlay_dimension(data.get(ATTR_WIDTH), 240, 1600),
        height=_optional_overlay_dimension(data.get(ATTR_HEIGHT), 120, 900),
        device_ids=device_ids,
    )


def _resolve_receiver(
    hass: Any,
    request: ShowCameraRequest | ShowNotificationRequest,
) -> ReceiverEntry:
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
        device_id=str(data[CONF_DEVICE_ID]),
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
    prefer_external: bool = False,
) -> ShowCameraCommand:
    if request.stream_type == STREAM_TYPE_SNAPSHOT:
        return ShowCameraCommand(
            title=title,
            url=_camera_snapshot_url(
                hass,
                request.camera_entity,
                prefer_external=prefer_external,
            ),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_SNAPSHOT,
            **_presentation_payload(request),
        )

    preview_url = _snapshot_preview_url(
        hass,
        request,
        prefer_external=prefer_external,
    )
    try:
        return ShowCameraCommand(
            title=title,
            url=await _async_camera_stream_url(
                hass,
                request.camera_entity,
                prefer_external=prefer_external,
            ),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_HLS,
            preview_url=preview_url,
            **_presentation_payload(request),
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
            url=_camera_snapshot_url(
                hass,
                request.camera_entity,
                prefer_external=prefer_external,
            ),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_SNAPSHOT,
            **_presentation_payload(request),
        )


def _snapshot_preview_url(
    hass: Any,
    request: ShowCameraRequest,
    *,
    prefer_external: bool = False,
) -> str | None:
    if request.stream_type == STREAM_TYPE_SNAPSHOT or not request.snapshot_fallback:
        return None

    preview_entity = request.snapshot_camera_entity or request.camera_entity
    _validate_camera_entity(hass, preview_entity)
    return _optional_camera_snapshot_url(
        hass,
        preview_entity,
        prefer_external=prefer_external,
    )


async def _async_camera_stream_url(
    hass: Any,
    entity_id: str,
    *,
    prefer_external: bool = False,
) -> str:
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

    absolute_url = _absolute_stream_url(
        hass,
        str(stream_url),
        prefer_external=prefer_external,
    )
    _LOGGER.debug("Resolved stream URL for %s to %s", entity_id, absolute_url)
    return absolute_url


def _absolute_stream_url(
    hass: Any,
    stream_url: str,
    *,
    prefer_external: bool = False,
) -> str:
    parsed = urlparse(stream_url)
    if parsed.scheme and parsed.netloc:
        return stream_url

    network_module = __import__(
        "homeassistant.helpers.network",
        fromlist=["get_url"],
    )
    try:
        base_url = network_module.get_url(hass, prefer_external=prefer_external)
    except TypeError:
        base_url = network_module.get_url(hass)

    return urljoin(f"{base_url.rstrip('/')}/", stream_url.lstrip("/"))


def _camera_title(hass: Any, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    friendly_name = state.attributes.get("friendly_name") if state is not None else None
    return str(friendly_name or entity_id)


def _camera_snapshot_url(
    hass: Any,
    entity_id: str,
    *,
    prefer_external: bool = False,
) -> str:
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
    return _absolute_stream_url(
        hass,
        f"{path}?{query}",
        prefer_external=prefer_external,
    )


def _optional_camera_snapshot_url(
    hass: Any,
    entity_id: str,
    *,
    prefer_external: bool = False,
) -> str | None:
    try:
        return _camera_snapshot_url(
            hass,
            entity_id,
            prefer_external=prefer_external,
        )
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


def _validated_color(value: Any, default: str) -> str:
    color = _optional_text(value) or default
    if not COLOR_PATTERN.fullmatch(color):
        raise ServiceValidationError("invalid_color")
    return color


def _notification_position(data: dict[str, Any]) -> str:
    position = str(data.get(ATTR_POSITION, "top_right")).strip().lower()
    if position not in NOTIFICATION_POSITIONS:
        raise ServiceValidationError("invalid_position")
    return position


def _notification_size(value: Any, minimum: int, maximum: int) -> int:
    size = int(value)
    if not minimum <= size <= maximum:
        raise ServiceValidationError("invalid_notification_size")
    return size


def _presentation_payload(request: ShowCameraRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if request.width is not None:
        payload["width"] = request.width
    if request.height is not None:
        payload["height"] = request.height
    if request.message is not None:
        payload.update(
            {
                "message": request.message,
                "position": request.position,
                "title_color": request.title_color,
                "title_size": request.title_size,
                "message_color": request.message_color,
                "message_size": request.message_size,
                "background_color": request.background_color,
            }
        )
    return payload


def _optional_overlay_dimension(value: Any, minimum: int, maximum: int) -> int | None:
    if value is None:
        return None
    size = int(value)
    if not minimum <= size <= maximum:
        raise ServiceValidationError("invalid_overlay_size")
    return size
