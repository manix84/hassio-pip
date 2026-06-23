"""Version helpers for HA TV PiP."""

from __future__ import annotations

import json
from pathlib import Path


def integration_version() -> str:
    """Return the installed Home Assistant integration version."""

    manifest_path = Path(__file__).with_name("manifest.json")
    try:
        with manifest_path.open(encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(manifest.get("version", "unknown"))


def version_alignment(receiver_version: str | None) -> dict[str, str | bool]:
    """Return a small summary of receiver/integration version parity."""

    integration = integration_version()
    receiver = receiver_version or "unknown"
    if integration == "unknown" or receiver == "unknown":
        state = "unknown"
        matched = False
        guidance = (
            "Unable to compare receiver and integration versions. Check both "
            "installed releases when troubleshooting."
        )
    elif _normalise_version(integration) == _normalise_version(receiver):
        state = "matched"
        matched = True
        guidance = "Receiver APK and Home Assistant integration versions match."
    else:
        state = "mismatch"
        matched = False
        guidance = (
            "Update the Android receiver APK and Home Assistant integration "
            "from the same HA TV PiP release."
        )

    return {
        "integration_version": integration,
        "receiver_version": receiver,
        "version_alignment": state,
        "versions_match": matched,
        "version_guidance": guidance,
    }


def _normalise_version(version: str) -> str:
    return version.strip().removeprefix("v")
