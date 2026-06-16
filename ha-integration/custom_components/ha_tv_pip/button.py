"""Button platform for HA TV PiP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import ShowCameraCommand, async_close_receiver, async_show_camera
from .const import CONF_TOKEN
from .entity import ReceiverEntity

if TYPE_CHECKING:

    class ButtonEntity:
        """Fallback base for unit tests outside Home Assistant."""


else:
    try:
        from homeassistant.components.button import ButtonEntity
    except ModuleNotFoundError:

        class ButtonEntity:
            """Fallback base for unit tests outside Home Assistant."""


TEST_STREAM_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


async def async_setup_entry(hass: Any, entry: Any, async_add_entities: Any) -> None:
    """Set up HA TV PiP receiver buttons."""

    async_add_entities(
        [
            ReceiverTestButton(entry),
            ReceiverCloseButton(entry),
        ]
    )


class ReceiverTestButton(ReceiverEntity, ButtonEntity):
    """Button that sends a known public HLS test stream to the receiver."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="test", name="Test")

    async def async_press(self) -> None:
        """Send a short test stream command."""

        await async_show_camera(
            self.host,
            self.port,
            token=str(self.entry.data[CONF_TOKEN]),
            command=ShowCameraCommand(
                title="HA TV PiP Test",
                url=TEST_STREAM_URL,
                duration_seconds=15,
                enter_pip=True,
                stream_type="hls",
            ),
        )


class ReceiverCloseButton(ReceiverEntity, ButtonEntity):
    """Button that closes the active receiver display."""

    def __init__(self, entry: Any) -> None:
        super().__init__(entry, key="close", name="Close")

    async def async_press(self) -> None:
        """Close the active display on the receiver."""

        await async_close_receiver(
            self.host,
            self.port,
            token=str(self.entry.data[CONF_TOKEN]),
        )
