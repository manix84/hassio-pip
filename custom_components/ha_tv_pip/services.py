"""Home Assistant services for HA TV PiP."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode, urljoin, urlparse

from .client import (
    ReceiverCapabilities,
    ReceiverClientError,
    ReceiverStatus,
    ShowCameraCommand,
    async_close_receiver,
    async_get_receiver_status,
    async_show_camera,
)
from .const import (
    CONF_CAMERA_DEFAULTS,
    CONF_DEFAULT_DURATION_SECONDS,
    CONF_DEFAULT_HEIGHT,
    CONF_DEFAULT_POSITION,
    CONF_DEFAULT_SNAPSHOT_FALLBACK,
    CONF_DEFAULT_STREAM_TYPE,
    CONF_DEFAULT_WIDTH,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_PREFER_REMOTE_TRANSPORT,
    CONF_TOKEN,
    DOMAIN,
    NOTIFICATION_POSITIONS,
    SERVICE_CALIBRATE_CAMERA,
    SERVICE_CLEAR_ALL_CAMERA_DEFAULTS,
    SERVICE_CLEAR_CAMERA_DEFAULTS,
    SERVICE_SAVE_RESTREAM_SOURCE,
    SERVICE_SET_CAMERA_DEFAULTS,
    SERVICE_SHOW_CAMERA,
    SERVICE_SHOW_NOTIFICATION,
    SERVICE_SHOW_SNAPSHOT,
    SERVICE_SUGGEST_RESTREAM_SOURCE,
    SERVICE_TEST_CAMERA_STREAM,
    STREAM_TYPE_AUTO,
    STREAM_TYPE_HLS,
    STREAM_TYPE_MJPEG,
    STREAM_TYPE_MJPEG_FIRST,
    STREAM_TYPE_NOTIFICATION,
    STREAM_TYPE_SNAPSHOT,
    STREAM_TYPES,
)
from .remote import remote_registry
from .restreaming import restreaming_provider_metadata

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
ATTR_AREA_ID = "area_id"
ATTR_DEVICE_ID = "device_id"
ATTR_DURATION_SECONDS = "duration_seconds"
ATTR_ENTER_PIP = "enter_pip"
ATTR_ENTITY_ID = "entity_id"
ATTR_FLOOR_ID = "floor_id"
ATTR_BACKGROUND_COLOR = "background_color"
ATTR_HEIGHT = "height"
ATTR_LABEL_ID = "label_id"
ATTR_MESSAGE = "message"
ATTR_MESSAGE_COLOR = "message_color"
ATTR_MESSAGE_SIZE = "message_size"
ATTR_POSITION = "position"
ATTR_SNAPSHOT_CAMERA_ENTITY = "snapshot_camera_entity"
ATTR_SNAPSHOT_FALLBACK = "snapshot_fallback"
ATTR_SAVE = "save"
ATTR_SAVE_RECOMMENDATION = "save_recommendation"
ATTR_RESTREAM_PROVIDER = "restream_provider"
ATTR_RESTREAM_URL = "restream_url"
ATTR_STREAM_CAMERA_ENTITY = "stream_camera_entity"
ATTR_STREAM_TYPE = "stream_type"
ATTR_TEXT_OVERLAY = "text_overlay"
ATTR_TITLE = "title"
ATTR_TITLE_COLOR = "title_color"
ATTR_TITLE_SIZE = "title_size"
ATTR_WIDTH = "width"
CAMERA_COMPATIBILITY_KEY = "camera_compatibility"
CAMERA_LAST_RESULT_KEY = "camera_last_result"
LAST_COMMAND_RESULT_KEY = "last_command_result"
LAST_COMMAND_RESULT_LISTENERS_KEY = "last_command_result_listeners"
LAST_COMMAND_RESULT_SIGNAL = f"{DOMAIN}_last_command_result"
CAMERA_DOMAIN = "camera"
COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
DEFAULT_NOTIFICATION_BACKGROUND_COLOR = "#B30F0E0E"
DEFAULT_NOTIFICATION_MESSAGE_COLOR = "#fbf5f5"
DEFAULT_NOTIFICATION_TITLE = "Home Assistant"
DEFAULT_NOTIFICATION_TITLE_COLOR = "#50BFF2"
ERROR_MESSAGES = {
    "camera_not_found": "Camera entity was not found.",
    "camera_stream_unavailable": (
        "Home Assistant could not create an HLS stream for the camera."
    ),
    "camera_mjpeg_unavailable": (
        "Home Assistant could not create an MJPEG stream URL for the camera."
    ),
    "invalid_camera_entity": "The selected entity is not a camera.",
    "invalid_duration": "Duration must be at least 1 second.",
    "invalid_color": (
        "Notification colors must be six-digit or eight-digit hex values."
    ),
    "invalid_notification_size": (
        "Notification text sizes are outside the supported range."
    ),
    "invalid_overlay_size": "Overlay width or height is outside the supported range.",
    "invalid_position": (
        "Notification position must be top_right, top_left, bottom_right, "
        "or bottom_left."
    ),
    "invalid_restream_url": (
        "Restream URL must be an absolute http or https URL."
    ),
    "invalid_stream_type": (
        "Stream type must be auto, hls, mjpeg, mjpeg_first, or snapshot."
    ),
    "receiver_capability_unavailable": (
        "The selected receiver does not report support for the requested feature."
    ),
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
    "unsupported_target_type": (
        "HA TV PiP actions must target a paired receiver device. Use "
        "target.device_id and choose an HA TV PiP receiver."
    ),
}
TARGET_ATTRS = (
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    ATTR_AREA_ID,
    ATTR_LABEL_ID,
    ATTR_FLOOR_ID,
)
UNSUPPORTED_TARGET_ATTRS = (
    ATTR_ENTITY_ID,
    ATTR_AREA_ID,
    ATTR_LABEL_ID,
    ATTR_FLOOR_ID,
)


@dataclass(frozen=True)
class ReceiverEntry:
    """Minimal receiver config entry data required by services."""

    entry_id: str
    device_id: str
    name: str
    host: str
    port: int
    token: str
    options: dict[str, Any]


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
    text_overlay: bool
    width: int | None
    height: int | None
    snapshot_camera_entity: str | None
    snapshot_fallback: bool
    restream_provider: str | None
    restream_url: str | None
    stream_camera_entity: str | None
    stream_type: str
    title: str | None
    device_ids: tuple[str, ...]
    duration_explicit: bool = False
    position_explicit: bool = False
    snapshot_camera_entity_explicit: bool = False
    snapshot_fallback_explicit: bool = False
    restream_provider_explicit: bool = False
    restream_url_explicit: bool = False
    stream_camera_entity_explicit: bool = False
    stream_type_explicit: bool = False
    width_explicit: bool = False
    height_explicit: bool = False


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
    duration_explicit: bool = False
    position_explicit: bool = False
    width_explicit: bool = False
    height_explicit: bool = False


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

    target_schema = {
        vol.Optional(attr): vol.Any(str, [str], None) for attr in TARGET_ATTRS
    }

    base_schema = {
        **target_schema,
        vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
        vol.Optional(ATTR_ENTER_PIP, default=True): bool,
        vol.Optional(ATTR_TITLE): str,
        vol.Optional(ATTR_MESSAGE): str,
        vol.Optional(ATTR_POSITION): vol.Any(*NOTIFICATION_POSITIONS),
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
        vol.Optional(ATTR_TEXT_OVERLAY, default=False): bool,
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
            vol.Optional(ATTR_SNAPSHOT_FALLBACK): bool,
            vol.Optional(ATTR_RESTREAM_PROVIDER): str,
            vol.Optional(ATTR_RESTREAM_URL): str,
            vol.Optional(ATTR_STREAM_CAMERA_ENTITY): cv.entity_id,
            vol.Optional(ATTR_STREAM_TYPE): vol.Any(*STREAM_TYPES),
            vol.Optional(ATTR_DURATION_SECONDS): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
        }
    )
    camera_defaults_fields = {
        **target_schema,
        vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
        vol.Optional(ATTR_SNAPSHOT_CAMERA_ENTITY): cv.entity_id,
        vol.Optional(ATTR_SNAPSHOT_FALLBACK): bool,
        vol.Optional(ATTR_RESTREAM_PROVIDER): str,
        vol.Optional(ATTR_RESTREAM_URL): str,
        vol.Optional(ATTR_STREAM_CAMERA_ENTITY): cv.entity_id,
        vol.Optional(ATTR_STREAM_TYPE): vol.Any(*STREAM_TYPES),
        vol.Optional(ATTR_DURATION_SECONDS): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=3600),
        ),
        vol.Optional(ATTR_POSITION): vol.Any(*NOTIFICATION_POSITIONS),
        vol.Optional(ATTR_WIDTH): vol.All(
            vol.Coerce(int),
            vol.Range(min=240, max=1600),
        ),
        vol.Optional(ATTR_HEIGHT): vol.All(
            vol.Coerce(int),
            vol.Range(min=120, max=900),
        ),
    }
    camera_defaults_schema = vol.Schema(camera_defaults_fields)
    camera_test_schema = vol.Schema(
        {
            **camera_defaults_fields,
            vol.Optional(ATTR_SAVE_RECOMMENDATION, default=False): bool,
        }
    )
    camera_calibration_schema = vol.Schema(
        {
            **camera_defaults_fields,
            vol.Optional(ATTR_SAVE, default=False): bool,
        }
    )
    save_restream_schema = vol.Schema(
        {
            **target_schema,
            vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
            vol.Required(ATTR_RESTREAM_URL): str,
            vol.Optional(ATTR_RESTREAM_PROVIDER, default="go2rtc"): str,
            vol.Optional(ATTR_SNAPSHOT_CAMERA_ENTITY): cv.entity_id,
            vol.Optional(ATTR_SNAPSHOT_FALLBACK, default=True): bool,
            vol.Optional(ATTR_STREAM_TYPE): vol.Any(
                STREAM_TYPE_HLS,
                STREAM_TYPE_MJPEG,
            ),
            vol.Optional(ATTR_DURATION_SECONDS): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
            vol.Optional(ATTR_POSITION): vol.Any(*NOTIFICATION_POSITIONS),
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
    snapshot_schema = vol.Schema(
        {
            **base_schema,
            vol.Optional(ATTR_DURATION_SECONDS): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
        }
    )
    notification_schema = vol.Schema(
        {
            **target_schema,
            vol.Optional(ATTR_TITLE, default=DEFAULT_NOTIFICATION_TITLE): str,
            vol.Optional(ATTR_MESSAGE): str,
            vol.Optional(ATTR_DURATION_SECONDS): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=3600),
            ),
            vol.Optional(ATTR_ENTER_PIP, default=True): bool,
            vol.Optional(ATTR_POSITION): vol.Any(*NOTIFICATION_POSITIONS),
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

    async def handle_test_camera_stream(call: Any) -> dict[str, Any]:
        return await async_handle_test_camera_stream(hass, call)

    async def handle_calibrate_camera(call: Any) -> dict[str, Any]:
        return await async_handle_calibrate_camera(hass, call)

    async def handle_set_camera_defaults(call: Any) -> dict[str, Any]:
        return await async_handle_set_camera_defaults(hass, call)

    async def handle_save_restream_source(call: Any) -> dict[str, Any]:
        return await async_handle_save_restream_source(hass, call)

    async def handle_clear_camera_defaults(call: Any) -> dict[str, Any]:
        return await async_handle_clear_camera_defaults(hass, call)

    async def handle_clear_all_camera_defaults(call: Any) -> dict[str, Any]:
        return await async_handle_clear_all_camera_defaults(hass, call)

    async def handle_suggest_restream_source(call: Any) -> dict[str, Any]:
        return await async_handle_suggest_restream_source(hass, call)

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

    response_kwargs = _service_response_kwargs()

    if not hass.services.has_service(DOMAIN, SERVICE_TEST_CAMERA_STREAM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TEST_CAMERA_STREAM,
            handle_test_camera_stream,
            schema=camera_test_schema,
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CALIBRATE_CAMERA):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CALIBRATE_CAMERA,
            handle_calibrate_camera,
            schema=camera_calibration_schema,
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_CAMERA_DEFAULTS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CAMERA_DEFAULTS,
            handle_set_camera_defaults,
            schema=camera_defaults_schema,
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SAVE_RESTREAM_SOURCE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SAVE_RESTREAM_SOURCE,
            handle_save_restream_source,
            schema=save_restream_schema,
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_CAMERA_DEFAULTS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_CAMERA_DEFAULTS,
            handle_clear_camera_defaults,
            schema=vol.Schema(
                {
                    **target_schema,
                    vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
                }
            ),
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_ALL_CAMERA_DEFAULTS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_ALL_CAMERA_DEFAULTS,
            handle_clear_all_camera_defaults,
            schema=vol.Schema(target_schema),
            **response_kwargs,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SUGGEST_RESTREAM_SOURCE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SUGGEST_RESTREAM_SOURCE,
            handle_suggest_restream_source,
            schema=vol.Schema(
                {
                    **target_schema,
                    vol.Required(ATTR_CAMERA_ENTITY): cv.entity_id,
                    vol.Optional(ATTR_RESTREAM_PROVIDER, default="go2rtc"): str,
                }
            ),
            **response_kwargs,
        )


async def async_handle_show_camera(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_camera` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    if request.stream_camera_entity is not None:
        _validate_camera_entity(hass, request.stream_camera_entity)
    receiver = _resolve_receiver(hass, request)
    request = _apply_camera_defaults(request, receiver, duration_fallback=30)
    title = request.title or _camera_title(hass, request.camera_entity)
    remote = remote_registry(hass)
    prefer_external = _prefer_remote_transport(receiver, remote)
    capabilities = await _async_receiver_capabilities(receiver)
    request = _degrade_camera_request_for_capabilities(request, capabilities)
    try:
        _validate_camera_capabilities(request, capabilities)
    except ServiceValidationError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_CAMERA,
                stage="capability_check",
                reason=error.code,
                detail=error.detail,
                transport="remote" if prefer_external else "local",
            ),
        )
        raise
    try:
        command = await _async_show_camera_command(
            hass,
            request,
            title=title,
            prefer_external=prefer_external,
            capabilities=capabilities,
        )
    except ServiceValidationError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_CAMERA,
                stage="command_resolution",
                reason=error.code,
                detail=error.detail,
                transport="remote" if prefer_external else "local",
            ),
        )
        raise
    _LOGGER.info(
        "Sending camera %s to receiver %s using %s transport and %s stream",
        request.camera_entity,
        receiver.name,
        "remote" if prefer_external else "local",
        command.stream_type,
    )

    try:
        transport = await _async_send_receiver_command(
            receiver,
            remote,
            command,
            prefer_remote=prefer_external,
        )
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="accepted",
                command_type=SERVICE_SHOW_CAMERA,
                stage="receiver_command",
                transport=transport,
                command=command,
            ),
        )
    except ReceiverClientError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_CAMERA,
                stage="receiver_command",
                reason="receiver_command_failed",
                detail=str(error),
                transport="remote" if prefer_external else "local",
                command=command,
            ),
        )
        _LOGGER.error("Unable to send camera stream to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


async def async_handle_show_snapshot(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_snapshot` service calls."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    request = _apply_camera_defaults(request, receiver, duration_fallback=10)
    remote = remote_registry(hass)
    prefer_external = _prefer_remote_transport(receiver, remote)
    capabilities = await _async_receiver_capabilities(receiver)
    request = _degrade_camera_request_for_capabilities(request, capabilities)
    try:
        _validate_stream_capability(capabilities, STREAM_TYPE_SNAPSHOT)
    except ServiceValidationError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_SNAPSHOT,
                stage="capability_check",
                reason=error.code,
                detail=error.detail,
                transport="remote" if prefer_external else "local",
            ),
        )
        raise
    try:
        snapshot_url = _camera_snapshot_url(
            hass,
            request.camera_entity,
            prefer_external=prefer_external,
        )
    except ServiceValidationError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_SNAPSHOT,
                stage="command_resolution",
                reason=error.code,
                detail=error.detail,
                transport="remote" if prefer_external else "local",
            ),
        )
        raise
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
        transport = await _async_send_receiver_command(
            receiver,
            remote,
            command,
            prefer_remote=prefer_external,
        )
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="accepted",
                command_type=SERVICE_SHOW_SNAPSHOT,
                stage="receiver_command",
                transport=transport,
                command=command,
            ),
        )
    except ReceiverClientError as error:
        _store_camera_action_result(
            hass,
            receiver,
            _camera_action_result(
                request,
                receiver=receiver,
                status="failed",
                command_type=SERVICE_SHOW_SNAPSHOT,
                stage="receiver_command",
                reason="receiver_command_failed",
                detail=str(error),
                transport="remote" if prefer_external else "local",
                command=command,
            ),
        )
        _LOGGER.error("Unable to send camera snapshot to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


async def async_handle_show_notification(hass: Any, call: Any) -> None:
    """Handle `ha_tv_pip.show_notification` service calls."""

    request = _notification_request_from_call(call)
    receiver = _resolve_receiver(hass, request)
    request = _apply_notification_defaults(request, receiver)
    remote = remote_registry(hass)
    prefer_external = _prefer_remote_transport(receiver, remote)
    capabilities = await _async_receiver_capabilities(receiver)
    try:
        _validate_notification_capabilities(capabilities)
    except ServiceValidationError as error:
        _store_command_result(
            hass,
            receiver,
            _notification_action_result(
                request,
                receiver=receiver,
                status="failed",
                stage="capability_check",
                transport="remote" if prefer_external else "local",
                reason=error.code,
                detail=error.detail,
            ),
        )
        raise
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
            show_notification=True,
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
        transport = await _async_send_receiver_command(
            receiver,
            remote,
            command,
            prefer_remote=prefer_external,
        )
        _store_command_result(
            hass,
            receiver,
            _notification_action_result(
                request,
                receiver=receiver,
                status="accepted",
                stage="receiver_command",
                transport=transport,
                command=command,
            ),
        )
    except ReceiverClientError as error:
        _store_command_result(
            hass,
            receiver,
            _notification_action_result(
                request,
                receiver=receiver,
                status="failed",
                stage="receiver_command",
                transport="remote" if prefer_external else "local",
                command=command,
                reason="receiver_command_failed",
                detail=str(error),
            ),
        )
        _LOGGER.error("Unable to send notification to %s: %s", receiver.name, error)
        raise ServiceValidationError("receiver_command_failed", str(error)) from error


async def async_handle_test_camera_stream(hass: Any, call: Any) -> dict[str, Any]:
    """Resolve camera stream options and store a non-sensitive compatibility result."""

    return await _async_handle_camera_compatibility_workflow(
        hass,
        call,
        save_field=ATTR_SAVE_RECOMMENDATION,
        include_summary=False,
    )


async def async_handle_calibrate_camera(hass: Any, call: Any) -> dict[str, Any]:
    """Calibrate camera stream defaults for a receiver."""

    return await _async_handle_camera_compatibility_workflow(
        hass,
        call,
        save_field=ATTR_SAVE,
        include_summary=True,
    )


async def _async_handle_camera_compatibility_workflow(
    hass: Any,
    call: Any,
    *,
    save_field: str,
    include_summary: bool,
) -> dict[str, Any]:
    """Run a compatibility test and optionally save its recommended defaults."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    if request.stream_camera_entity is not None:
        _validate_camera_entity(hass, request.stream_camera_entity)
    if request.snapshot_camera_entity is not None:
        _validate_camera_entity(hass, request.snapshot_camera_entity)

    receiver = _resolve_receiver(hass, request)
    request = _apply_camera_defaults(request, receiver, duration_fallback=30)
    remote = remote_registry(hass)
    prefer_external = _prefer_remote_transport(receiver, remote)
    capabilities = await _async_receiver_capabilities(receiver)
    result = await _async_camera_compatibility_report(
        hass,
        request,
        receiver=receiver,
        prefer_external=prefer_external,
        capabilities=capabilities,
    )
    if bool(getattr(call, "data", {}).get(save_field, False)):
        saved_defaults = _save_camera_recommendation_defaults(
            hass,
            receiver,
            request,
            result,
        )
        result = {
            **result,
            "saved_as_defaults": bool(saved_defaults),
            "saved_defaults": saved_defaults,
        }
    elif include_summary:
        result = {
            **result,
            "saved_as_defaults": False,
        }
    result = {
        **result,
        "action_plan": _camera_compatibility_action_plan(request, result),
    }
    if include_summary:
        result = {
            **result,
            "summary": _camera_calibration_summary(result),
        }
    _store_camera_compatibility(hass, receiver, request.camera_entity, result)
    return result


async def async_handle_set_camera_defaults(hass: Any, call: Any) -> dict[str, Any]:
    """Persist per-camera defaults for a receiver."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    if request.stream_camera_entity is not None:
        _validate_camera_entity(hass, request.stream_camera_entity)
    if request.snapshot_camera_entity is not None:
        _validate_camera_entity(hass, request.snapshot_camera_entity)

    receiver = _resolve_receiver(hass, request)
    defaults = _camera_defaults_payload(request)
    _save_camera_defaults(hass, receiver, request.camera_entity, defaults)
    return {
        "accepted": True,
        "camera_entity": request.camera_entity,
        "receiver": receiver.name,
        "defaults": defaults,
    }


async def async_handle_save_restream_source(hass: Any, call: Any) -> dict[str, Any]:
    """Persist a tested restream URL as the camera's TV-safe live source."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    if request.snapshot_camera_entity is not None:
        _validate_camera_entity(hass, request.snapshot_camera_entity)

    if request.restream_url is None:
        raise ServiceValidationError("invalid_restream_url")

    receiver = _resolve_receiver(hass, request)
    stream_type = _restream_url_stream_type(request)
    defaults: dict[str, Any] = {
        ATTR_RESTREAM_PROVIDER: request.restream_provider or "go2rtc",
        ATTR_RESTREAM_URL: request.restream_url,
        ATTR_SNAPSHOT_FALLBACK: request.snapshot_fallback,
        ATTR_STREAM_TYPE: stream_type,
    }
    if request.snapshot_camera_entity is not None:
        defaults[ATTR_SNAPSHOT_CAMERA_ENTITY] = request.snapshot_camera_entity
    if request.duration_explicit and request.duration_seconds is not None:
        defaults[ATTR_DURATION_SECONDS] = request.duration_seconds
    if request.position_explicit:
        defaults[ATTR_POSITION] = request.position
    if request.width_explicit and request.width is not None:
        defaults[ATTR_WIDTH] = request.width
    if request.height_explicit and request.height is not None:
        defaults[ATTR_HEIGHT] = request.height

    _save_camera_defaults(hass, receiver, request.camera_entity, defaults)
    return {
        "accepted": True,
        "camera_entity": request.camera_entity,
        "receiver": receiver.name,
        "defaults": defaults,
        "next_action": {
            "service": SERVICE_SHOW_CAMERA,
            "data": {ATTR_CAMERA_ENTITY: request.camera_entity},
        },
    }


async def async_handle_clear_camera_defaults(hass: Any, call: Any) -> dict[str, Any]:
    """Remove per-camera defaults for a receiver."""

    request = _request_from_call(call)
    _validate_camera_entity(hass, request.camera_entity)
    receiver = _resolve_receiver(hass, request)
    entry = _entry_for_receiver(hass, receiver.entry_id)
    options = dict(getattr(entry, "options", {}) or {})
    camera_defaults = dict(options.get(CONF_CAMERA_DEFAULTS, {}) or {})
    removed = camera_defaults.pop(request.camera_entity, None) is not None
    if camera_defaults:
        options[CONF_CAMERA_DEFAULTS] = camera_defaults
    else:
        options.pop(CONF_CAMERA_DEFAULTS, None)
    _update_entry_options(hass, entry, options)
    return {
        "accepted": True,
        "camera_entity": request.camera_entity,
        "receiver": receiver.name,
        "removed": removed,
    }


async def async_handle_clear_all_camera_defaults(
    hass: Any,
    call: Any,
) -> dict[str, Any]:
    """Remove all per-camera defaults for a receiver."""

    receiver = _resolve_receiver_from_target(hass, call)
    entry = _entry_for_receiver(hass, receiver.entry_id)
    options = dict(getattr(entry, "options", {}) or {})
    camera_defaults = options.pop(CONF_CAMERA_DEFAULTS, {})
    cleared_cameras = (
        sorted(camera_defaults) if isinstance(camera_defaults, dict) else []
    )
    _update_entry_options(hass, entry, options)
    return {
        "accepted": True,
        "receiver": receiver.name,
        "cleared_camera_count": len(cleared_cameras),
        "cleared_cameras": cleared_cameras,
    }


async def async_handle_suggest_restream_source(
    hass: Any,
    call: Any,
) -> dict[str, Any]:
    """Suggest manual restream setup values for a camera and receiver."""

    data = dict(getattr(call, "data", {}))
    camera_entity = str(data.get(ATTR_CAMERA_ENTITY, "")).strip()
    if not camera_entity:
        raise ServiceValidationError("missing_camera_entity")
    _validate_camera_entity(hass, camera_entity)

    receiver = _resolve_receiver_from_target(hass, call)
    provider = _optional_text(data.get(ATTR_RESTREAM_PROVIDER)) or "go2rtc"
    if provider != "go2rtc":
        provider = "manual"

    return _restream_source_suggestion(hass, receiver, camera_entity, provider)


def _request_from_call(call: Any) -> ShowCameraRequest:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    _reject_unsupported_target_types(data, target)
    device_ids = _tuple_value(target.get(ATTR_DEVICE_ID) or data.get(ATTR_DEVICE_ID))

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
        text_overlay=bool(data.get(ATTR_TEXT_OVERLAY, False)),
        width=_optional_overlay_dimension(data.get(ATTR_WIDTH), 240, 1600),
        height=_optional_overlay_dimension(data.get(ATTR_HEIGHT), 120, 900),
        title=_optional_text(data.get(ATTR_TITLE)),
        snapshot_camera_entity=_optional_text(data.get(ATTR_SNAPSHOT_CAMERA_ENTITY)),
        snapshot_fallback=bool(data.get(ATTR_SNAPSHOT_FALLBACK, True)),
        restream_provider=_optional_text(data.get(ATTR_RESTREAM_PROVIDER)),
        restream_url=_validated_restream_url(data.get(ATTR_RESTREAM_URL)),
        stream_camera_entity=_optional_text(data.get(ATTR_STREAM_CAMERA_ENTITY)),
        stream_type=stream_type,
        device_ids=device_ids,
        duration_explicit=ATTR_DURATION_SECONDS in data,
        position_explicit=ATTR_POSITION in data,
        snapshot_camera_entity_explicit=ATTR_SNAPSHOT_CAMERA_ENTITY in data,
        snapshot_fallback_explicit=ATTR_SNAPSHOT_FALLBACK in data,
        restream_provider_explicit=ATTR_RESTREAM_PROVIDER in data,
        restream_url_explicit=ATTR_RESTREAM_URL in data,
        stream_camera_entity_explicit=ATTR_STREAM_CAMERA_ENTITY in data,
        stream_type_explicit=ATTR_STREAM_TYPE in data,
        width_explicit=ATTR_WIDTH in data,
        height_explicit=ATTR_HEIGHT in data,
    )


def _notification_request_from_call(call: Any) -> ShowNotificationRequest:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    _reject_unsupported_target_types(data, target)
    device_ids = _tuple_value(target.get(ATTR_DEVICE_ID) or data.get(ATTR_DEVICE_ID))
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
        duration_explicit=ATTR_DURATION_SECONDS in data,
        position_explicit=ATTR_POSITION in data,
        width_explicit=ATTR_WIDTH in data,
        height_explicit=ATTR_HEIGHT in data,
    )


def _resolve_receiver(
    hass: Any,
    request: ShowCameraRequest | ShowNotificationRequest,
) -> ReceiverEntry:
    return _resolve_receiver_from_device_ids(hass, request.device_ids)


def _resolve_receiver_from_target(hass: Any, call: Any) -> ReceiverEntry:
    data = dict(getattr(call, "data", {}))
    target = getattr(call, "target", {}) or {}
    _reject_unsupported_target_types(data, target)
    device_ids = _tuple_value(target.get(ATTR_DEVICE_ID) or data.get(ATTR_DEVICE_ID))
    return _resolve_receiver_from_device_ids(hass, device_ids)


def _resolve_receiver_from_device_ids(
    hass: Any,
    device_ids: tuple[str, ...],
) -> ReceiverEntry:
    entries = _configured_entries(hass)
    if device_ids:
        entries = _entries_for_devices(hass, entries, device_ids)

    if not entries:
        _LOGGER.warning(
            "No receiver matched service target devices: %s",
            device_ids,
        )
        raise ServiceValidationError("receiver_not_found")

    if len(entries) > 1:
        _LOGGER.warning(
            "Service call matched multiple receivers; target a specific receiver device"
        )
        raise ServiceValidationError("multiple_receivers")

    entry = entries[0]
    return _resolve_receiver_from_entry(entry)


def _resolve_receiver_from_entry(entry: Any) -> ReceiverEntry:
    """Build a receiver command target from a config entry."""

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
        options=dict(getattr(entry, "options", {}) or {}),
    )


def _prefer_remote_transport(receiver: ReceiverEntry, remote: Any) -> bool:
    """Return whether receiver commands should prefer the remote transport."""

    return bool(
        receiver.options.get(CONF_PREFER_REMOTE_TRANSPORT, False)
        and remote.is_connected(receiver.device_id)
    )


async def _async_send_receiver_command(
    receiver: ReceiverEntry,
    remote: Any,
    command: ShowCameraCommand,
    *,
    prefer_remote: bool,
) -> str:
    """Send a receiver command with remote/local fallback ordering."""

    if prefer_remote and await remote.async_send_show(
        device_id=receiver.device_id,
        command=command,
    ):
        return "remote"

    if not prefer_remote:
        try:
            await async_show_camera(
                receiver.host,
                receiver.port,
                token=receiver.token,
                command=command,
            )
            return "local"
        except ReceiverClientError:
            if await remote.async_send_show(
                device_id=receiver.device_id,
                command=command,
            ):
                return "remote"
            raise

    await async_show_camera(
        receiver.host,
        receiver.port,
        token=receiver.token,
        command=command,
    )
    return "local"


async def _async_close_receiver_command(
    receiver: ReceiverEntry,
    remote: Any,
    *,
    prefer_remote: bool,
) -> tuple[bool, str]:
    """Close a receiver display with remote/local fallback ordering."""

    if prefer_remote and await remote.async_send_close(device_id=receiver.device_id):
        return True, "remote"

    if not prefer_remote:
        try:
            accepted = await async_close_receiver(
                receiver.host,
                receiver.port,
                token=receiver.token,
            )
            return accepted, "local"
        except ReceiverClientError:
            if await remote.async_send_close(device_id=receiver.device_id):
                return True, "remote"
            raise

    accepted = await async_close_receiver(
        receiver.host,
        receiver.port,
        token=receiver.token,
    )
    return accepted, "local"


async def _async_get_receiver_status_command(
    receiver: ReceiverEntry,
    remote: Any,
    *,
    prefer_remote: bool,
) -> tuple[ReceiverStatus, str]:
    """Fetch receiver status with remote/local fallback ordering."""

    if prefer_remote:
        status = await remote.async_get_status(device_id=receiver.device_id)
        if status is not None:
            return status, "remote"

    if not prefer_remote:
        try:
            status = await async_get_receiver_status(receiver.host, receiver.port)
            return status, "local"
        except ReceiverClientError:
            status = await remote.async_get_status(device_id=receiver.device_id)
            if status is not None:
                return status, "remote"
            raise

    status = await async_get_receiver_status(receiver.host, receiver.port)
    return status, "local"


def _configured_entries(hass: Any) -> list[Any]:
    config_entries = getattr(hass, "config_entries", None)
    if config_entries is None:
        data_entries = getattr(hass, "data", {}).get(DOMAIN, {}).get("entries", {})
        return list(data_entries.values())
    return list(config_entries.async_entries(DOMAIN))


def _entry_for_receiver(hass: Any, entry_id: str) -> Any:
    for entry in _configured_entries(hass):
        if entry.entry_id == entry_id:
            return entry
    raise ServiceValidationError("receiver_not_found")


def _update_entry_options(hass: Any, entry: Any, options: dict[str, Any]) -> None:
    config_entries = getattr(hass, "config_entries", None)
    if config_entries is not None and hasattr(config_entries, "async_update_entry"):
        config_entries.async_update_entry(entry, options=options)
        return
    entry.options = options


def _apply_camera_defaults(
    request: ShowCameraRequest,
    receiver: ReceiverEntry,
    *,
    duration_fallback: int,
) -> ShowCameraRequest:
    """Apply receiver-level defaults without overriding explicit service data."""

    updates: dict[str, Any] = {}
    camera_defaults = _camera_defaults(receiver.options, request.camera_entity)
    duration = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_DURATION_SECONDS,
        minimum=1,
        maximum=3600,
    )
    width = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_WIDTH,
        minimum=240,
        maximum=1600,
    )
    height = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_HEIGHT,
        minimum=120,
        maximum=900,
    )
    stream_type = str(receiver.options.get(CONF_DEFAULT_STREAM_TYPE, "")).strip()
    position = str(receiver.options.get(CONF_DEFAULT_POSITION, "")).strip()

    if not request.duration_explicit:
        updates["duration_seconds"] = (
            _camera_default_int(
                camera_defaults,
                ATTR_DURATION_SECONDS,
                minimum=1,
                maximum=3600,
            )
            or duration
            or duration_fallback
        )
    if not request.position_explicit:
        camera_position = str(camera_defaults.get(ATTR_POSITION, "")).strip()
        if camera_position in NOTIFICATION_POSITIONS:
            updates["position"] = camera_position
        elif position in NOTIFICATION_POSITIONS:
            updates["position"] = position
    if (
        not request.snapshot_camera_entity_explicit
        and _optional_text(camera_defaults.get(ATTR_SNAPSHOT_CAMERA_ENTITY)) is not None
    ):
        updates["snapshot_camera_entity"] = _optional_text(
            camera_defaults.get(ATTR_SNAPSHOT_CAMERA_ENTITY)
        )
    if not request.snapshot_fallback_explicit and (
        ATTR_SNAPSHOT_FALLBACK in camera_defaults
        or CONF_DEFAULT_SNAPSHOT_FALLBACK in receiver.options
    ):
        updates["snapshot_fallback"] = bool(
            camera_defaults.get(
                ATTR_SNAPSHOT_FALLBACK,
                receiver.options.get(CONF_DEFAULT_SNAPSHOT_FALLBACK),
            )
        )
    if (
        not request.stream_camera_entity_explicit
        and _optional_text(camera_defaults.get(ATTR_STREAM_CAMERA_ENTITY)) is not None
    ):
        updates["stream_camera_entity"] = _optional_text(
            camera_defaults.get(ATTR_STREAM_CAMERA_ENTITY)
        )
    if (
        not request.restream_provider_explicit
        and _optional_text(camera_defaults.get(ATTR_RESTREAM_PROVIDER)) is not None
    ):
        updates["restream_provider"] = _optional_text(
            camera_defaults.get(ATTR_RESTREAM_PROVIDER)
        )
    if (
        not request.restream_url_explicit
        and _validated_restream_url(camera_defaults.get(ATTR_RESTREAM_URL)) is not None
    ):
        updates["restream_url"] = _validated_restream_url(
            camera_defaults.get(ATTR_RESTREAM_URL)
        )
    if not request.stream_type_explicit:
        camera_stream_type = str(camera_defaults.get(ATTR_STREAM_TYPE, "")).strip()
        if camera_stream_type in STREAM_TYPES:
            updates["stream_type"] = camera_stream_type
        elif stream_type in STREAM_TYPES:
            updates["stream_type"] = stream_type
    if not request.width_explicit:
        updates["width"] = (
            _camera_default_int(
                camera_defaults,
                ATTR_WIDTH,
                minimum=240,
                maximum=1600,
            )
            or width
            or request.width
        )
    if not request.height_explicit:
        updates["height"] = (
            _camera_default_int(
                camera_defaults,
                ATTR_HEIGHT,
                minimum=120,
                maximum=900,
            )
            or height
            or request.height
        )

    return replace(request, **updates) if updates else request


def _apply_notification_defaults(
    request: ShowNotificationRequest,
    receiver: ReceiverEntry,
) -> ShowNotificationRequest:
    """Apply receiver-level popup defaults to notification service calls."""

    updates: dict[str, Any] = {}
    duration = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_DURATION_SECONDS,
        minimum=1,
        maximum=3600,
    )
    width = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_WIDTH,
        minimum=240,
        maximum=1600,
    )
    height = _receiver_default_int(
        receiver.options,
        CONF_DEFAULT_HEIGHT,
        minimum=120,
        maximum=900,
    )
    position = str(receiver.options.get(CONF_DEFAULT_POSITION, "")).strip()

    if not request.duration_explicit:
        updates["duration_seconds"] = duration or 15
    if not request.position_explicit and position in NOTIFICATION_POSITIONS:
        updates["position"] = position
    if not request.width_explicit and width is not None:
        updates["width"] = width
    if not request.height_explicit and height is not None:
        updates["height"] = height

    return replace(request, **updates) if updates else request


def _receiver_default_int(
    options: dict[str, Any],
    key: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    try:
        value = int(options.get(key, 0) or 0)
    except (TypeError, ValueError):
        return None
    if not minimum <= value <= maximum:
        return None
    return value


def _camera_defaults(options: dict[str, Any], camera_entity: str) -> dict[str, Any]:
    all_defaults = options.get(CONF_CAMERA_DEFAULTS)
    if not isinstance(all_defaults, dict):
        return {}
    defaults = all_defaults.get(camera_entity)
    return defaults if isinstance(defaults, dict) else {}


def _camera_default_int(
    defaults: dict[str, Any],
    key: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    try:
        value = int(defaults.get(key, 0) or 0)
    except (TypeError, ValueError):
        return None
    if not minimum <= value <= maximum:
        return None
    return value


def _camera_defaults_payload(request: ShowCameraRequest) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    if request.duration_explicit and request.duration_seconds is not None:
        defaults[ATTR_DURATION_SECONDS] = request.duration_seconds
    if request.position_explicit:
        defaults[ATTR_POSITION] = request.position
    if request.snapshot_camera_entity_explicit and request.snapshot_camera_entity:
        defaults[ATTR_SNAPSHOT_CAMERA_ENTITY] = request.snapshot_camera_entity
    if request.snapshot_fallback_explicit:
        defaults[ATTR_SNAPSHOT_FALLBACK] = request.snapshot_fallback
    if request.restream_provider_explicit and request.restream_provider:
        defaults[ATTR_RESTREAM_PROVIDER] = request.restream_provider
    if request.restream_url_explicit and request.restream_url:
        defaults[ATTR_RESTREAM_URL] = request.restream_url
    if request.stream_camera_entity_explicit and request.stream_camera_entity:
        defaults[ATTR_STREAM_CAMERA_ENTITY] = request.stream_camera_entity
    if request.stream_type_explicit:
        defaults[ATTR_STREAM_TYPE] = request.stream_type
    if request.width_explicit and request.width is not None:
        defaults[ATTR_WIDTH] = request.width
    if request.height_explicit and request.height is not None:
        defaults[ATTR_HEIGHT] = request.height
    return defaults


def _save_camera_defaults(
    hass: Any,
    receiver: ReceiverEntry,
    camera_entity: str,
    defaults: dict[str, Any],
) -> None:
    entry = _entry_for_receiver(hass, receiver.entry_id)
    options = dict(getattr(entry, "options", {}) or {})
    camera_defaults = dict(options.get(CONF_CAMERA_DEFAULTS, {}) or {})
    camera_defaults[camera_entity] = defaults
    options[CONF_CAMERA_DEFAULTS] = camera_defaults
    _update_entry_options(hass, entry, options)


def _save_camera_recommendation_defaults(
    hass: Any,
    receiver: ReceiverEntry,
    request: ShowCameraRequest,
    result: dict[str, Any],
) -> dict[str, Any]:
    defaults = _recommended_camera_defaults_payload(request, result)
    if not defaults:
        return {}
    entry = _entry_for_receiver(hass, receiver.entry_id)
    options = dict(getattr(entry, "options", {}) or {})
    camera_defaults = dict(options.get(CONF_CAMERA_DEFAULTS, {}) or {})
    camera_defaults[request.camera_entity] = defaults
    options[CONF_CAMERA_DEFAULTS] = camera_defaults
    _update_entry_options(hass, entry, options)
    return defaults


def _recommended_camera_defaults_payload(
    request: ShowCameraRequest,
    result: dict[str, Any],
) -> dict[str, Any]:
    recommended = str(result.get("recommended_stream_type") or "").strip()
    if recommended not in STREAM_TYPES:
        return {}

    defaults = _camera_defaults_payload(request)
    defaults[ATTR_STREAM_TYPE] = recommended
    return defaults


def _camera_calibration_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Build a concise user-facing calibration summary."""

    recommended = result.get("recommended_stream_type")
    saved = bool(result.get("saved_as_defaults", False))
    compatible = recommended is not None
    provider_metadata = result.get("restreaming_provider")
    summary = {
        "compatible": compatible,
        "recommended_stream_type": recommended,
        "recommendation_reason": result.get("recommendation_reason"),
        "restreaming_recommended": bool(
            result.get("restreaming_recommended", False)
        ),
        "restreaming_reason": result.get("restreaming_reason"),
        "restreaming_next_step": result.get("restreaming_next_step"),
        "restreaming_options": result.get("restreaming_options", []),
        "saved": saved,
        "next_step": _camera_calibration_next_step(compatible, saved),
    }
    action_plan = result.get("action_plan")
    if isinstance(action_plan, dict):
        summary["primary_action"] = action_plan.get("primary_action")
        summary["primary_action_label"] = action_plan.get("primary_action_label")
    if bool(result.get("has_restream_url", False)):
        summary["has_restream_url"] = True
    if result.get("restream_provider") is not None:
        summary["restream_provider"] = result.get("restream_provider")
    if isinstance(provider_metadata, dict):
        summary["restreaming_provider_status"] = provider_metadata.get("status")
        summary["restreaming_provider_next_step"] = provider_metadata.get(
            "next_step"
        )
    return summary


def _camera_calibration_next_step(compatible: bool, saved: bool) -> str:
    if not compatible:
        return "try_different_camera_entity_or_stream_source"
    if saved:
        return "use_show_camera_without_repeating_defaults"
    return "review_recommended_defaults_or_run_again_with_save"


def _camera_compatibility_action_plan(
    request: ShowCameraRequest,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Return concrete next actions for a camera compatibility result."""

    recommended = result.get("recommended_stream_type")
    saved = bool(result.get("saved_as_defaults", False))
    recommended_defaults = dict(result.get("recommended_defaults", {}) or {})
    camera_data = {ATTR_CAMERA_ENTITY: request.camera_entity}

    if saved:
        return {
            "primary_action": "use_saved_defaults",
            "primary_action_label": "Use show_camera without repeating defaults",
            "service": SERVICE_SHOW_CAMERA,
            "data": camera_data,
            "notes": [
                "Per-camera defaults are saved for this receiver.",
                (
                    "Future automations only need the camera entity unless "
                    "overriding defaults."
                ),
            ],
        }

    if result.get("restreaming_reason") == (
        "snapshot_only_live_stream_restreaming_recommended"
    ):
        return {
            "primary_action": "use_snapshot_or_configure_live_source",
            "primary_action_label": (
                "Use snapshot alerts now, or configure a TV-safe live source"
            ),
            "service": SERVICE_SET_CAMERA_DEFAULTS,
            "data": {
                ATTR_CAMERA_ENTITY: request.camera_entity,
                ATTR_STREAM_TYPE: STREAM_TYPE_SNAPSHOT,
            },
            "fields_to_try": [
                ATTR_STREAM_CAMERA_ENTITY,
                ATTR_RESTREAM_URL,
                ATTR_RESTREAM_PROVIDER,
            ],
            "provider_help": _restreaming_provider_help(result),
            "notes": [
                "Snapshot is available, but live HLS/MJPEG was not available.",
                "Try a lower-resolution camera entity or a TV-safe HLS/MJPEG restream.",
            ],
        }

    if recommended in STREAM_TYPES and recommended_defaults:
        service_data = {
            ATTR_CAMERA_ENTITY: request.camera_entity,
            **_action_plan_safe_defaults(recommended_defaults),
        }
        return {
            "primary_action": "save_recommended_defaults",
            "primary_action_label": "Save the recommended per-camera defaults",
            "service": SERVICE_SET_CAMERA_DEFAULTS,
            "data": service_data,
            "notes": [
                "Review recommended_defaults before saving.",
                (
                    "After saving, call show_camera with only camera_entity "
                    "for normal use."
                ),
            ],
        }

    return {
        "primary_action": "check_camera_access_or_configure_live_source",
        "primary_action_label": (
            "Check camera access or configure a TV-safe stream source"
        ),
        "service": SERVICE_CALIBRATE_CAMERA,
        "data": camera_data,
        "fields_to_try": [
            ATTR_STREAM_CAMERA_ENTITY,
            ATTR_SNAPSHOT_CAMERA_ENTITY,
            ATTR_RESTREAM_URL,
            ATTR_RESTREAM_PROVIDER,
        ],
        "provider_help": _restreaming_provider_help(result),
        "notes": [
            (
                "Home Assistant could not resolve a supported HLS, MJPEG, "
                "or snapshot path."
            ),
            (
                "Check camera permissions, try another camera entity, or "
                "configure a restream."
            ),
        ],
    }


def _restreaming_provider_help(result: dict[str, Any]) -> dict[str, Any]:
    """Return provider helper metadata for camera compatibility action plans."""

    provider_metadata = result.get("restreaming_provider")
    if not isinstance(provider_metadata, dict):
        return {}

    provider_help = {
        "status": provider_metadata.get("status"),
        "next_step": provider_metadata.get("next_step"),
        "documentation_url": provider_metadata.get("documentation_url"),
        "manual_provider_workflows": provider_metadata.get(
            "manual_provider_workflows", []
        ),
        "future_provider_workflows": provider_metadata.get(
            "future_provider_workflows", []
        ),
    }
    return {
        key: value
        for key, value in provider_help.items()
        if value is not None and value != []
    }


def _restream_source_suggestion(
    hass: Any,
    receiver: ReceiverEntry,
    camera_entity: str,
    provider: str,
) -> dict[str, Any]:
    """Return manual restream setup guidance for a selected camera."""

    metadata = restreaming_provider_metadata()
    candidate_stream_names = _candidate_restream_names(
        camera_entity,
        _camera_title(hass, camera_entity),
    )
    url_patterns = _provider_url_patterns(provider, candidate_stream_names)
    primary_stream_name = candidate_stream_names[0]
    return {
        "accepted": True,
        "camera_entity": camera_entity,
        "camera_title": _camera_title(hass, camera_entity),
        "receiver": receiver.name,
        "receiver_device_id": receiver.device_id,
        "provider": provider,
        "provider_status": metadata.get("status"),
        "candidate_stream_names": candidate_stream_names,
        "candidate_urls": url_patterns,
        "recommended_test_order": [
            "Test candidate HLS URLs from a browser on the TV network.",
            "If HLS fails, test the matching MJPEG URL.",
            "Save the first TV-safe URL that plays reliably.",
        ],
        "save_action": {
            "service": SERVICE_SAVE_RESTREAM_SOURCE,
            "target": {ATTR_DEVICE_ID: receiver.device_id},
            "data": {
                ATTR_CAMERA_ENTITY: camera_entity,
                ATTR_RESTREAM_PROVIDER: provider,
                ATTR_RESTREAM_URL: (
                    f"<tested {provider} HLS or MJPEG URL for {primary_stream_name}>"
                ),
                ATTR_SNAPSHOT_FALLBACK: True,
            },
        },
        "provider_help": {
            "status": metadata.get("status"),
            "next_step": metadata.get("next_step"),
            "documentation_url": metadata.get("documentation_url"),
            "manual_provider_workflows": metadata.get(
                "manual_provider_workflows", []
            ),
            "future_provider_workflows": metadata.get(
                "future_provider_workflows", []
            ),
        },
    }


def _candidate_restream_names(camera_entity: str, camera_title: str) -> list[str]:
    object_id = camera_entity.split(".", 1)[-1]
    candidates = [
        _slug_like_name(object_id),
        _slug_like_name(camera_title),
    ]
    expanded: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        expanded.append(candidate)
        if "_" in candidate:
            expanded.append(candidate.replace("_", "-"))
    return list(dict.fromkeys(expanded))


def _slug_like_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug


def _provider_url_patterns(
    provider: str,
    stream_names: list[str],
) -> list[dict[str, str]]:
    if provider != "go2rtc":
        return [
            {
                "stream_name": stream_name,
                "hls": (
                    f"<{provider} HLS URL for stream '{stream_name}'>"
                ),
                "mjpeg": (
                    f"<{provider} MJPEG URL for stream '{stream_name}'>"
                ),
            }
            for stream_name in stream_names
        ]

    return [
        {
            "stream_name": stream_name,
            "hls": (
                "http://homeassistant.local:1984/api/stream.m3u8?"
                f"src={quote(stream_name)}"
            ),
            "mjpeg": (
                "http://homeassistant.local:1984/api/stream.mjpeg?"
                f"src={quote(stream_name)}"
            ),
        }
        for stream_name in stream_names
    ]


def _action_plan_safe_defaults(defaults: dict[str, Any]) -> dict[str, Any]:
    """Return recommended defaults without duplicating sensitive direct URLs."""

    safe_defaults = dict(defaults)
    if ATTR_RESTREAM_URL in safe_defaults:
        safe_defaults[ATTR_RESTREAM_URL] = "<see recommended_defaults.restream_url>"
    return safe_defaults


async def _async_camera_compatibility_report(
    hass: Any,
    request: ShowCameraRequest,
    *,
    receiver: ReceiverEntry,
    prefer_external: bool,
    capabilities: ReceiverCapabilities | None,
) -> dict[str, Any]:
    stream_entity = request.stream_camera_entity or request.camera_entity
    snapshot_entity = request.snapshot_camera_entity or request.camera_entity
    if request.restream_url is not None:
        restream_type = _restream_url_stream_type(request)
        supports_hls = _supports_stream(capabilities, STREAM_TYPE_HLS)
        supports_mjpeg = _supports_stream(capabilities, STREAM_TYPE_MJPEG)
        results = [
            {
                "stream_type": STREAM_TYPE_HLS,
                "available": restream_type == STREAM_TYPE_HLS and supports_hls,
                "reason": "receiver_capability_unavailable"
                if restream_type == STREAM_TYPE_HLS and not supports_hls
                else None,
                "source": "restream_url" if restream_type == STREAM_TYPE_HLS else None,
            },
            {
                "stream_type": STREAM_TYPE_MJPEG,
                "available": restream_type == STREAM_TYPE_MJPEG and supports_mjpeg,
                "reason": "receiver_capability_unavailable"
                if restream_type == STREAM_TYPE_MJPEG and not supports_mjpeg
                else None,
                "source": "restream_url"
                if restream_type == STREAM_TYPE_MJPEG
                else None,
            },
            await _async_stream_probe(
                STREAM_TYPE_SNAPSHOT,
                lambda: _camera_snapshot_url(
                    hass,
                    snapshot_entity,
                    prefer_external=prefer_external,
                ),
                capabilities,
            ),
        ]
        results = [
            {key: value for key, value in result.items() if value is not None}
            for result in results
        ]
    else:
        results = [
            await _async_stream_probe(
                STREAM_TYPE_HLS,
                lambda: _async_camera_stream_url(
                    hass,
                    stream_entity,
                    prefer_external=prefer_external,
                ),
                capabilities,
            ),
            await _async_stream_probe(
                STREAM_TYPE_MJPEG,
                lambda: _camera_mjpeg_stream_url(
                    hass,
                    stream_entity,
                    prefer_external=prefer_external,
                ),
                capabilities,
            ),
            await _async_stream_probe(
                STREAM_TYPE_SNAPSHOT,
                lambda: _camera_snapshot_url(
                    hass,
                    snapshot_entity,
                    prefer_external=prefer_external,
                ),
                capabilities,
            ),
        ]
    recommended, recommendation_reason = _recommended_stream_type(
        results,
        capabilities,
    )
    restreaming_guidance = _restreaming_guidance(
        results,
        recommended,
    )
    restreaming_provider = (
        restreaming_provider_metadata()
        if bool(restreaming_guidance.get("restreaming_recommended", False))
        else None
    )
    result: dict[str, Any] = {
        "camera_entity": request.camera_entity,
        "stream_camera_entity": stream_entity,
        "snapshot_camera_entity": snapshot_entity,
        "receiver": receiver.name,
        "receiver_device_id": receiver.device_id,
        "tested_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "preferred_stream_type": request.stream_type,
        "recommended_stream_type": recommended,
        "recommendation_reason": recommendation_reason,
        "stream_source": _camera_stream_source(request),
        "restream_provider": request.restream_provider,
        **restreaming_guidance,
        "restreaming_provider": restreaming_provider,
        "results": results,
    }
    if request.restream_url is not None:
        result["has_restream_url"] = True
    result["recommended_defaults"] = _recommended_camera_defaults_payload(
        request,
        result,
    )
    return {
        key: value
        for key, value in result.items()
        if value is not None and value != {}
    }


async def _async_stream_probe(
    stream_type: str,
    resolver: Any,
    capabilities: ReceiverCapabilities | None,
) -> dict[str, Any]:
    if not _supports_stream(capabilities, stream_type):
        return {
            "stream_type": stream_type,
            "available": False,
            "reason": "receiver_capability_unavailable",
        }
    try:
        resolved = resolver()
        if hasattr(resolved, "__await__"):
            resolved = await resolved
    except ServiceValidationError as error:
        return {
            "stream_type": stream_type,
            "available": False,
            "reason": error.code,
        }
    return {
        "stream_type": stream_type,
        "available": bool(resolved),
    }


def _recommended_stream_type(
    results: list[dict[str, Any]],
    capabilities: ReceiverCapabilities | None,
) -> tuple[str | None, str]:
    available = {
        str(result["stream_type"])
        for result in results
        if bool(result.get("available", False))
    }
    if STREAM_TYPE_HLS in available and STREAM_TYPE_MJPEG in available:
        if _supports_playable_fallback(capabilities):
            return STREAM_TYPE_AUTO, "hls_available_with_mjpeg_playable_fallback"
        return STREAM_TYPE_MJPEG_FIRST, "mjpeg_first_reduces_receiver_decoder_risk"
    if STREAM_TYPE_HLS in available:
        return STREAM_TYPE_HLS, "hls_available"
    if STREAM_TYPE_MJPEG in available:
        return STREAM_TYPE_MJPEG, "mjpeg_available"
    if STREAM_TYPE_SNAPSHOT in available:
        return STREAM_TYPE_SNAPSHOT, "snapshot_available"
    return None, "no_compatible_stream_available"


def _restreaming_guidance(
    results: list[dict[str, Any]],
    recommended_stream_type: str | None,
) -> dict[str, Any]:
    """Return guidance for cameras that likely need a restreamed TV-safe source."""

    available = {
        str(result["stream_type"])
        for result in results
        if bool(result.get("available", False))
    }
    has_live_stream = bool({STREAM_TYPE_HLS, STREAM_TYPE_MJPEG} & available)
    if has_live_stream:
        return {"restreaming_recommended": False}
    if recommended_stream_type == STREAM_TYPE_SNAPSHOT:
        return {
            "restreaming_recommended": True,
            "restreaming_reason": (
                "snapshot_only_live_stream_restreaming_recommended"
            ),
            "restreaming_next_step": "configure_tv_safe_live_stream_source",
            "restreaming_options": [
                "try_stream_camera_entity",
                "try_lower_resolution_profile",
                "try_mjpeg_or_h264_substream",
                "try_go2rtc_or_webrtc_bridge",
                "wait_for_transcoding_support",
            ],
        }
    return {
        "restreaming_recommended": True,
        "restreaming_reason": "no_supported_stream_paths_restreaming_recommended",
        "restreaming_next_step": "check_camera_access_or_configure_tv_safe_source",
        "restreaming_options": [
            "check_camera_entity_access",
            "try_different_camera_entity",
            "try_lower_resolution_profile",
            "try_go2rtc_or_webrtc_bridge",
            "wait_for_transcoding_support",
        ],
    }


def _store_camera_compatibility(
    hass: Any,
    receiver: ReceiverEntry,
    camera_entity: str,
    result: dict[str, Any],
) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    compatibility = data.setdefault(CAMERA_COMPATIBILITY_KEY, {})
    receiver_results = compatibility.setdefault(receiver.entry_id, {})
    receiver_results[camera_entity] = result


def _camera_action_result(
    request: ShowCameraRequest,
    *,
    receiver: ReceiverEntry,
    status: str,
    command_type: str,
    stage: str,
    transport: str,
    command: ShowCameraCommand | None = None,
    reason: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Build a redacted last camera action result for entity state/diagnostics."""

    result: dict[str, Any] = {
        "command_type": command_type,
        "camera_entity": request.camera_entity,
        "stream_camera_entity": request.stream_camera_entity or request.camera_entity,
        "snapshot_camera_entity": request.snapshot_camera_entity
        or request.camera_entity,
        "restream_provider": request.restream_provider,
        "receiver": receiver.name,
        "receiver_device_id": receiver.device_id,
        "requested_stream_type": request.stream_type,
        "stream_source": _camera_stream_source(request),
        "snapshot_fallback": request.snapshot_fallback,
        "status": status,
        "stage": stage,
        "transport": transport,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    if request.restream_url is not None:
        result["has_restream_url"] = True
    if command is not None:
        result.update(
            {
                "final_stream_type": command.stream_type,
                "has_preview": command.preview_url is not None,
                "has_playable_fallback": command.fallback_url is not None,
                "playable_fallback_stream_type": command.fallback_stream_type,
                "position": command.position,
                "width": command.width,
                "height": command.height,
                "has_notification_text": (
                    command.show_notification or command.message is not None
                ),
            }
        )
    if reason is not None:
        result["reason"] = reason
    if detail is not None:
        result["detail"] = detail
    return {key: value for key, value in result.items() if value is not None}


def _camera_stream_source(request: ShowCameraRequest) -> str:
    if request.restream_url is not None:
        return "restream_url"
    if request.stream_type == STREAM_TYPE_SNAPSHOT:
        if request.snapshot_camera_entity:
            return "snapshot_camera_entity"
        return "camera_entity"
    if request.stream_camera_entity:
        return "stream_camera_entity"
    return "camera_entity"


def _store_camera_action_result(
    hass: Any,
    receiver: ReceiverEntry,
    result: dict[str, Any],
) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    action_results = data.setdefault(CAMERA_LAST_RESULT_KEY, {})
    action_results[receiver.entry_id] = result
    _store_command_result(hass, receiver, result)


def _notification_action_result(
    request: ShowNotificationRequest,
    *,
    receiver: ReceiverEntry,
    status: str,
    stage: str,
    transport: str,
    command: ShowCameraCommand | None = None,
    reason: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command_type": SERVICE_SHOW_NOTIFICATION,
        "receiver": receiver.name,
        "receiver_device_id": receiver.device_id,
        "status": status,
        "stage": stage,
        "transport": transport,
        "title": request.title,
        "has_message": request.message is not None,
        "position": request.position,
        "width": request.width,
        "height": request.height,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    if command is not None:
        result.update(
            {
                "final_stream_type": command.stream_type,
                "has_notification_text": (
                    command.show_notification or command.message is not None
                ),
            }
        )
    if reason is not None:
        result["reason"] = reason
    if detail is not None:
        result["detail"] = detail
    return {key: value for key, value in result.items() if value is not None}


def _store_command_result(
    hass: Any,
    receiver: ReceiverEntry,
    result: dict[str, Any],
) -> None:
    store_last_command_result(hass, receiver.entry_id, result)


def store_last_command_result(
    hass: Any,
    entry_id: str,
    result: dict[str, Any],
) -> None:
    """Store the latest receiver command result and notify interested entities."""

    data = hass.data.setdefault(DOMAIN, {})
    command_results = data.setdefault(LAST_COMMAND_RESULT_KEY, {})
    command_results[entry_id] = result
    listeners = data.get(LAST_COMMAND_RESULT_LISTENERS_KEY, {}).get(entry_id, [])
    for listener in list(listeners):
        listener()
    _send_last_command_result_signal(hass, entry_id)


def last_command_result_signal(entry_id: str) -> str:
    return f"{LAST_COMMAND_RESULT_SIGNAL}_{entry_id}"


def _send_last_command_result_signal(hass: Any, entry_id: str) -> None:
    try:
        dispatcher = __import__(
            "homeassistant.helpers.dispatcher",
            fromlist=["async_dispatcher_send"],
        )
    except ModuleNotFoundError:
        return

    dispatcher.async_dispatcher_send(hass, last_command_result_signal(entry_id))


def _service_response_kwargs() -> dict[str, Any]:
    try:
        core = __import__("homeassistant.core", fromlist=["SupportsResponse"])
    except ModuleNotFoundError:
        return {}
    supports_response = getattr(core, "SupportsResponse", None)
    if supports_response is None:
        return {}
    response_value = getattr(supports_response, "ONLY", None)
    return {"supports_response": response_value} if response_value is not None else {}


def _entries_for_devices(
    hass: Any,
    entries: list[Any],
    device_ids: tuple[str, ...],
) -> list[Any]:
    device_id_set = set(device_ids)
    direct_matches = [
        entry
        for entry in entries
        if entry.entry_id in device_id_set
        or str(entry.data.get(CONF_DEVICE_ID, "")) in device_id_set
    ]
    if direct_matches:
        return direct_matches

    matched_entry_ids: set[str] = set()
    try:
        device_registry_module = __import__(
            "homeassistant.helpers.device_registry",
            fromlist=["async_get"],
        )
        device_registry = device_registry_module.async_get(hass)
        for device_id in device_ids:
            device = device_registry.async_get(device_id)
            if device is None:
                continue
            matched_entry_ids.update(device.config_entries)
    except ModuleNotFoundError:
        _LOGGER.debug("Home Assistant device registry is unavailable")

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
    capabilities: ReceiverCapabilities | None = None,
) -> ShowCameraCommand:
    if request.stream_type == STREAM_TYPE_SNAPSHOT:
        _validate_stream_capability(capabilities, STREAM_TYPE_SNAPSHOT)
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

    stream_entity = request.stream_camera_entity or request.camera_entity
    preview_url = _snapshot_preview_url(
        hass,
        request,
        prefer_external=prefer_external,
    )
    if request.restream_url is not None:
        stream_type = _restream_url_stream_type(request)
        _validate_stream_capability(capabilities, stream_type)
        return ShowCameraCommand(
            title=title,
            url=request.restream_url,
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=stream_type,
            preview_url=preview_url,
            **_presentation_payload(request),
        )

    supports_mjpeg = _supports_stream(capabilities, STREAM_TYPE_MJPEG)
    supports_hls = _supports_stream(capabilities, STREAM_TYPE_HLS)
    supports_snapshot = _supports_stream(capabilities, STREAM_TYPE_SNAPSHOT)

    if request.stream_type == STREAM_TYPE_MJPEG:
        _validate_stream_capability(capabilities, STREAM_TYPE_MJPEG)

    if request.stream_type == STREAM_TYPE_HLS:
        _validate_stream_capability(capabilities, STREAM_TYPE_HLS)

    if request.stream_type in (STREAM_TYPE_MJPEG, STREAM_TYPE_MJPEG_FIRST) and (
        supports_mjpeg or capabilities is None
    ):
        try:
            return _mjpeg_show_camera_command(
                hass,
                request,
                title=title,
                stream_entity=stream_entity,
                preview_url=preview_url,
                prefer_external=prefer_external,
            )
        except ServiceValidationError as error:
            if (
                request.stream_type == STREAM_TYPE_MJPEG
                or error.code != "camera_mjpeg_unavailable"
            ):
                raise
            _LOGGER.warning(
                "Falling back to HLS for %s because MJPEG stream resolution failed: %s",
                stream_entity,
                error,
            )

    if (
        request.stream_type == STREAM_TYPE_AUTO
        and supports_mjpeg
        and not _supports_playable_fallback(capabilities)
    ):
        try:
            _LOGGER.info(
                "Using MJPEG first for %s because receiver does not support "
                "playable fallback",
                stream_entity,
            )
            return _mjpeg_show_camera_command(
                hass,
                request,
                title=title,
                stream_entity=stream_entity,
                preview_url=preview_url,
                prefer_external=prefer_external,
            )
        except ServiceValidationError as error:
            if error.code != "camera_mjpeg_unavailable":
                raise
            _LOGGER.warning(
                "Falling back to HLS for %s because automatic MJPEG "
                "resolution failed: %s",
                stream_entity,
                error,
            )

    try:
        if request.stream_type == STREAM_TYPE_AUTO and not supports_hls:
            raise ServiceValidationError("camera_stream_unavailable")

        fallback_url = None
        if (
            request.stream_type == STREAM_TYPE_AUTO
            and supports_mjpeg
            and _supports_playable_fallback(capabilities)
        ):
            fallback_url = _optional_camera_mjpeg_stream_url(
                hass,
                stream_entity,
                prefer_external=prefer_external,
            )
        return ShowCameraCommand(
            title=title,
            url=await _async_camera_stream_url(
                hass,
                stream_entity,
                prefer_external=prefer_external,
            ),
            duration_seconds=request.duration_seconds,
            enter_pip=request.enter_pip,
            stream_type=STREAM_TYPE_HLS,
            preview_url=preview_url,
            fallback_url=fallback_url,
            fallback_stream_type=STREAM_TYPE_MJPEG if fallback_url else None,
            **_presentation_payload(request),
        )
    except ServiceValidationError as error:
        if (
            request.stream_type == STREAM_TYPE_HLS
            or error.code != "camera_stream_unavailable"
        ):
            raise

        if request.stream_type != STREAM_TYPE_MJPEG_FIRST and supports_mjpeg:
            try:
                _LOGGER.warning(
                    "Falling back to MJPEG for %s because HLS stream "
                    "resolution failed: %s",
                    stream_entity,
                    error,
                )
                return _mjpeg_show_camera_command(
                    hass,
                    request,
                    title=title,
                    stream_entity=stream_entity,
                    preview_url=preview_url,
                    prefer_external=prefer_external,
                )
            except ServiceValidationError as mjpeg_error:
                if mjpeg_error.code != "camera_mjpeg_unavailable":
                    raise

        if not supports_snapshot:
            raise

        _LOGGER.warning(
            "Falling back to snapshot for %s because compatible video streams failed.",
            stream_entity,
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


def _mjpeg_show_camera_command(
    hass: Any,
    request: ShowCameraRequest,
    *,
    title: str,
    stream_entity: str,
    preview_url: str | None,
    prefer_external: bool = False,
) -> ShowCameraCommand:
    return ShowCameraCommand(
        title=title,
        url=_camera_mjpeg_stream_url(
            hass,
            stream_entity,
            prefer_external=prefer_external,
        ),
        duration_seconds=request.duration_seconds,
        enter_pip=request.enter_pip,
        stream_type=STREAM_TYPE_MJPEG,
        preview_url=preview_url,
        **_presentation_payload(request),
    )


def _restream_url_stream_type(request: ShowCameraRequest) -> str:
    if request.stream_type == STREAM_TYPE_MJPEG:
        return STREAM_TYPE_MJPEG
    if request.stream_type == STREAM_TYPE_HLS:
        return STREAM_TYPE_HLS
    if request.restream_url is None:
        return STREAM_TYPE_HLS
    path = urlparse(request.restream_url).path.lower()
    if path.endswith(".mjpeg") or path.endswith(".mjpg") or "mjpeg" in path:
        return STREAM_TYPE_MJPEG
    return STREAM_TYPE_HLS


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


def _camera_mjpeg_stream_url(
    hass: Any,
    entity_id: str,
    *,
    prefer_external: bool = False,
) -> str:
    state = hass.states.get(entity_id)
    access_token = None if state is None else state.attributes.get("access_token")
    if not access_token:
        _LOGGER.error(
            "Camera entity %s does not expose an MJPEG stream access token",
            entity_id,
        )
        raise ServiceValidationError("camera_mjpeg_unavailable")

    path = f"/api/camera_proxy_stream/{quote(entity_id, safe='')}"
    query = urlencode({"token": str(access_token)})
    return _absolute_stream_url(
        hass,
        f"{path}?{query}",
        prefer_external=prefer_external,
    )


def _optional_camera_mjpeg_stream_url(
    hass: Any,
    entity_id: str,
    *,
    prefer_external: bool = False,
) -> str | None:
    try:
        return _camera_mjpeg_stream_url(
            hass,
            entity_id,
            prefer_external=prefer_external,
        )
    except ServiceValidationError as error:
        _LOGGER.warning(
            "MJPEG fallback unavailable for %s: %s",
            entity_id,
            error,
        )
        return None


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


async def _async_receiver_capabilities(
    receiver: ReceiverEntry,
) -> ReceiverCapabilities | None:
    try:
        status = await async_get_receiver_status(receiver.host, receiver.port)
    except ReceiverClientError as error:
        _LOGGER.debug(
            "Could not fetch receiver capabilities for %s: %s",
            receiver.name,
            error,
        )
        return None

    return status.capabilities


def _validate_camera_capabilities(
    request: ShowCameraRequest,
    capabilities: ReceiverCapabilities | None,
) -> None:
    if capabilities is None:
        return

    if request.stream_type == STREAM_TYPE_MJPEG_FIRST:
        if not any(
            _supports_stream(capabilities, stream_type)
            for stream_type in (
                STREAM_TYPE_MJPEG,
                STREAM_TYPE_HLS,
                STREAM_TYPE_SNAPSHOT,
            )
        ):
            raise ServiceValidationError("receiver_capability_unavailable")
    elif request.stream_type != STREAM_TYPE_AUTO:
        _validate_stream_capability(capabilities, request.stream_type)
    elif not any(
        _supports_stream(capabilities, stream_type)
        for stream_type in (STREAM_TYPE_HLS, STREAM_TYPE_MJPEG, STREAM_TYPE_SNAPSHOT)
    ):
        raise ServiceValidationError("receiver_capability_unavailable")

    if _media_text_payload(request) and not capabilities.media_with_notification_text:
        raise ServiceValidationError("receiver_capability_unavailable")


def _degrade_camera_request_for_capabilities(
    request: ShowCameraRequest,
    capabilities: ReceiverCapabilities | None,
) -> ShowCameraRequest:
    """Drop optional media text fields when an older receiver cannot render them."""

    if capabilities is None or capabilities.media_with_notification_text:
        return request
    if not _media_text_payload(request):
        return request

    _LOGGER.warning(
        "Receiver does not support media text footers; sending %s without title/message"
        " presentation fields",
        request.camera_entity,
    )
    return replace(
        request,
        message=None,
        title=None,
    )


def _validate_notification_capabilities(
    capabilities: ReceiverCapabilities | None,
) -> None:
    _validate_stream_capability(capabilities, STREAM_TYPE_NOTIFICATION)
    if capabilities is None:
        return
    if not capabilities.styled_notifications:
        raise ServiceValidationError("receiver_capability_unavailable")


def _validate_stream_capability(
    capabilities: ReceiverCapabilities | None,
    stream_type: str,
) -> None:
    if not _supports_stream(capabilities, stream_type):
        raise ServiceValidationError("receiver_capability_unavailable")


def _supports_stream(
    capabilities: ReceiverCapabilities | None,
    stream_type: str,
) -> bool:
    if capabilities is None:
        return True
    return stream_type in capabilities.stream_types


def _supports_playable_fallback(capabilities: ReceiverCapabilities | None) -> bool:
    return capabilities is None or capabilities.playable_fallback


def _tuple_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _reject_unsupported_target_types(
    data: dict[str, Any],
    target: dict[str, Any],
) -> None:
    for attr in UNSUPPORTED_TARGET_ATTRS:
        if _tuple_value(target.get(attr) or data.get(attr)):
            raise ServiceValidationError("unsupported_target_type")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validated_restream_url(value: Any) -> str | None:
    url = _optional_text(value)
    if url is None:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ServiceValidationError("invalid_restream_url")
    return url


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
    show_notification = request.title is not None or request.message is not None
    if show_notification:
        payload["show_notification"] = True
    if request.width is not None:
        payload["width"] = request.width
    if request.height is not None:
        payload["height"] = request.height
    if show_notification:
        payload.update(
            {
                "position": request.position,
                "title_color": request.title_color,
                "title_size": request.title_size,
                "text_overlay": request.text_overlay,
                "message_color": request.message_color,
                "message_size": request.message_size,
                "background_color": request.background_color,
            }
        )
        if request.message is not None:
            payload["message"] = request.message
    return payload


def _media_text_payload(request: ShowCameraRequest) -> bool:
    return request.title is not None or request.message is not None


def _optional_overlay_dimension(value: Any, minimum: int, maximum: int) -> int | None:
    if value is None:
        return None
    size = int(value)
    if not minimum <= size <= maximum:
        raise ServiceValidationError("invalid_overlay_size")
    return size
