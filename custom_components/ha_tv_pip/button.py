"""Button platform for HA TV PiP."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .client import (
    ReceiverClientError,
    ShowCameraCommand,
    async_open_receiver,
)
from .const import CONF_DEVICE_ID, CONF_NAME, CONF_TOKEN
from .entity import ReceiverEntity
from .remote import remote_registry
from .remote_setup import async_sync_remote_setup, has_remote_setup_options
from .services import (
    _async_close_receiver_command,
    _async_get_receiver_status_command,
    _async_send_receiver_command,
    _prefer_remote_transport,
    _resolve_receiver_from_entry,
    store_last_command_result,
)

if TYPE_CHECKING:

    class ButtonEntity:
        """Fallback base for unit tests outside Home Assistant."""

    class EntityCategory:
        """Fallback entity category for unit tests outside Home Assistant."""

        CONFIG = "config"

    class HomeAssistantError(Exception):
        """Fallback Home Assistant error for unit tests."""


else:
    try:
        from homeassistant.components.button import ButtonEntity
        from homeassistant.const import EntityCategory
        from homeassistant.exceptions import HomeAssistantError
    except ModuleNotFoundError:

        class ButtonEntity:
            """Fallback base for unit tests outside Home Assistant."""

        class EntityCategory:
            """Fallback entity category for unit tests outside Home Assistant."""

            CONFIG = "config"

        class HomeAssistantError(Exception):
            """Fallback Home Assistant error for unit tests."""


TEST_STREAM_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


async def async_setup_entry(hass: Any, entry: Any, async_add_entities: Any) -> None:
    """Set up HA TV PiP receiver buttons."""

    async_add_entities(
        [
            ReceiverOpenButton(hass, entry),
            ReceiverSyncRemoteButton(hass, entry),
            ReceiverRefreshStatusButton(hass, entry),
            ReceiverTestButton(hass, entry),
            ReceiverCloseButton(hass, entry),
        ]
    )


class ReceiverOpenButton(ReceiverEntity, ButtonEntity):
    """Button that opens the receiver management UI on the TV."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="open_launcher", name="Open Launcher")
        self.hass = hass
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Open the receiver app on the TV."""

        try:
            accepted = await async_open_receiver(
                self.host,
                self.port,
                token=str(self.entry.data[CONF_TOKEN]),
            )
        except ReceiverClientError as error:
            _store_button_result(
                self.hass,
                self.entry,
                command_type="open_launcher",
                status="failed",
                reason="receiver_command_failed",
                detail=str(error),
            )
            raise HomeAssistantError(
                f"Could not open receiver launcher: {error}"
            ) from error

        _store_button_result(
            self.hass,
            self.entry,
            command_type="open_launcher",
            status="accepted" if accepted else "failed",
            reason=None if accepted else "receiver_command_rejected",
        )


class ReceiverSyncRemoteButton(ReceiverEntity, ButtonEntity):
    """Button that retries remote receiver settings provisioning."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="sync_remote_config", name="Sync Remote Config")
        self.hass = hass
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        """Push the configured remote receiver settings to the TV."""

        if not has_remote_setup_options(self.entry):
            _store_button_result(
                self.hass,
                self.entry,
                command_type="sync_remote_config",
                status="failed",
                stage="validation",
                reason="remote_config_missing",
            )
            raise HomeAssistantError(
                "Configure remote receiver settings before syncing."
            )

        if not await async_sync_remote_setup(self.hass, self.entry):
            _store_button_result(
                self.hass,
                self.entry,
                command_type="sync_remote_config",
                status="failed",
                reason="receiver_command_failed",
            )
            raise HomeAssistantError(
                "Could not send remote receiver settings to the TV."
            )
        _store_button_result(
            self.hass,
            self.entry,
            command_type="sync_remote_config",
            status="accepted",
        )


class ReceiverRefreshStatusButton(ReceiverEntity, ButtonEntity):
    """Button that checks the receiver status endpoint on demand."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="refresh_status", name="Refresh Status")
        self.hass = hass

    async def async_press(self) -> None:
        """Fetch receiver status once and fail visibly when unreachable."""

        receiver = _resolve_receiver_from_entry(self.entry)
        remote = remote_registry(self.hass)
        prefer_remote = _prefer_remote_transport(receiver, remote)
        try:
            _, transport = await _async_get_receiver_status_command(
                receiver,
                remote,
                prefer_remote=prefer_remote,
            )
        except ReceiverClientError as error:
            _store_button_result(
                self.hass,
                self.entry,
                command_type="refresh_status",
                status="failed",
                reason="receiver_command_failed",
                detail=str(error),
            )
            raise HomeAssistantError(
                f"Could not refresh receiver status: {error}"
            ) from error
        _store_button_result(
            self.hass,
            self.entry,
            command_type="refresh_status",
            status="accepted",
            transport=transport,
        )


class ReceiverTestButton(ReceiverEntity, ButtonEntity):
    """Button that sends a known public HLS test stream to the receiver."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="test_pip", name="Test PiP")
        self.hass = hass

    async def async_press(self) -> None:
        """Send a short test stream command."""

        command = ShowCameraCommand(
            title="HA TV PiP Test",
            url=TEST_STREAM_URL,
            duration_seconds=15,
            enter_pip=True,
            stream_type="hls",
        )
        receiver = _resolve_receiver_from_entry(self.entry)
        remote = remote_registry(self.hass)
        prefer_remote = _prefer_remote_transport(receiver, remote)
        try:
            transport = await _async_send_receiver_command(
                receiver,
                remote,
                command=command,
                prefer_remote=prefer_remote,
            )
        except ReceiverClientError as error:
            _store_button_result(
                self.hass,
                self.entry,
                command_type="test_pip",
                status="failed",
                reason="receiver_command_failed",
                detail=str(error),
                final_stream_type=command.stream_type,
            )
            raise HomeAssistantError(f"Could not send test PiP: {error}") from error
        _store_button_result(
            self.hass,
            self.entry,
            command_type="test_pip",
            status="accepted",
            transport=transport,
            final_stream_type=command.stream_type,
        )


class ReceiverCloseButton(ReceiverEntity, ButtonEntity):
    """Button that closes the active receiver display."""

    def __init__(self, hass: Any, entry: Any) -> None:
        super().__init__(entry, key="close_pip", name="Close PiP")
        self.hass = hass

    async def async_press(self) -> None:
        """Close the active display on the receiver."""

        receiver = _resolve_receiver_from_entry(self.entry)
        remote = remote_registry(self.hass)
        prefer_remote = _prefer_remote_transport(receiver, remote)
        try:
            accepted, transport = await _async_close_receiver_command(
                receiver,
                remote,
                prefer_remote=prefer_remote,
            )
        except ReceiverClientError as error:
            _store_button_result(
                self.hass,
                self.entry,
                command_type="close_pip",
                status="failed",
                reason="receiver_command_failed",
                detail=str(error),
            )
            raise HomeAssistantError(f"Could not close PiP: {error}") from error
        _store_button_result(
            self.hass,
            self.entry,
            command_type="close_pip",
            status="accepted" if accepted else "failed",
            transport=transport,
            reason=None if accepted else "receiver_command_rejected",
        )


def _store_button_result(
    hass: Any,
    entry: Any,
    *,
    command_type: str,
    status: str,
    stage: str = "receiver_command",
    transport: str = "local",
    final_stream_type: str | None = None,
    reason: str | None = None,
    detail: str | None = None,
) -> None:
    if hass is None or not hasattr(hass, "data"):
        return
    result: dict[str, Any] = {
        "command_type": command_type,
        "receiver": entry.data.get(CONF_NAME, "HA TV PiP Receiver"),
        "receiver_device_id": entry.data[CONF_DEVICE_ID],
        "status": status,
        "stage": stage,
        "transport": transport,
        "final_stream_type": final_stream_type,
        "reason": reason,
        "detail": detail,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    store_last_command_result(
        hass,
        entry.entry_id,
        {key: value for key, value in result.items() if value is not None},
    )
