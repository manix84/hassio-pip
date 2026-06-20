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
    "use_restream_url",
    "save_per_camera_defaults",
]
RESTREAMING_PLANNED_PROVIDER_PATHS = [
    "go2rtc",
    "webrtc",
    "transcoding",
]
RESTREAMING_MANUAL_PROVIDER_WORKFLOWS: list[dict[str, Any]] = [
    {
        "provider": "go2rtc",
        "status": "manual_url_supported",
        "current_support": (
            "Save a known TV-safe go2rtc HLS or MJPEG URL as a per-camera "
            "restream_url."
        ),
        "service": "set_camera_defaults",
        "fields": [
            "camera_entity",
            "restream_provider",
            "restream_url",
            "stream_type",
            "snapshot_fallback",
        ],
        "example_url_patterns": [
            "http://homeassistant.local:1984/api/stream.m3u8?src=<stream_name>",
            "http://homeassistant.local:1984/api/stream.mjpeg?src=<stream_name>",
        ],
    },
]
RESTREAMING_FUTURE_PROVIDER_WORKFLOWS: list[dict[str, Any]] = [
    {
        "provider": "go2rtc",
        "status": "planned",
        "planned_support": "Guided setup and stream-source helpers.",
    },
    {
        "provider": "webrtc",
        "status": "research",
        "planned_support": (
            "Low-latency receiver path where Android TV and Home Assistant "
            "constraints allow it."
        ),
    },
    {
        "provider": "transcoding",
        "status": "research",
        "planned_support": (
            "Optional conversion of unsupported camera formats into "
            "receiver-compatible video."
        ),
    },
]

RESTREAMING_PROVIDER_METADATA: dict[str, Any] = {
    "enabled": False,
    "status": RESTREAMING_PROVIDER_STATUS,
    "configured_provider": None,
    "active_provider": None,
    "supported_providers": [],
    "planned_providers": RESTREAMING_PLANNED_PROVIDER_PATHS,
    "manual_provider_workflows": RESTREAMING_MANUAL_PROVIDER_WORKFLOWS,
    "future_provider_workflows": RESTREAMING_FUTURE_PROVIDER_WORKFLOWS,
    "recommended_current_paths": RESTREAMING_CURRENT_PATHS,
    "next_step": "configure_tv_safe_live_stream_source",
    "documentation_url": RESTREAMING_PROVIDER_DOCS_URL,
}


def restreaming_provider_metadata() -> dict[str, Any]:
    """Return a copy of the current restreaming provider metadata."""

    return dict(RESTREAMING_PROVIDER_METADATA)
