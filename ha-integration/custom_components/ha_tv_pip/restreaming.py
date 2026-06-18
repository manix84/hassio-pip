"""Restreaming provider metadata for HA TV PiP."""

from __future__ import annotations

from typing import Any

RESTREAMING_PROVIDER_STATUS = "planned"
RESTREAMING_PROVIDER_DOCS_URL = (
    "https://github.com/manix84/ha-tv-pip/blob/main/docs/camera-compatibility.md"
)
RESTREAMING_CURRENT_PATHS = [
    "use_stream_camera_entity",
    "use_mjpeg_first",
    "use_snapshot_fallback",
    "use_camera_substream",
    "save_per_camera_defaults",
]
RESTREAMING_PLANNED_PROVIDER_PATHS = [
    "go2rtc",
    "webrtc",
    "transcoding",
]

RESTREAMING_PROVIDER_METADATA: dict[str, Any] = {
    "enabled": False,
    "status": RESTREAMING_PROVIDER_STATUS,
    "configured_provider": None,
    "active_provider": None,
    "supported_providers": [],
    "planned_providers": RESTREAMING_PLANNED_PROVIDER_PATHS,
    "recommended_current_paths": RESTREAMING_CURRENT_PATHS,
    "next_step": "configure_tv_safe_live_stream_source",
    "documentation_url": RESTREAMING_PROVIDER_DOCS_URL,
}


def restreaming_provider_metadata() -> dict[str, Any]:
    """Return a copy of the current restreaming provider metadata."""

    return dict(RESTREAMING_PROVIDER_METADATA)
