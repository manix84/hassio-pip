from pathlib import Path

SERVICES_YAML = (
    Path(__file__).parents[1]
    / "custom_components"
    / "ha_tv_pip"
    / "services.yaml"
)

SERVICE_EXAMPLES: dict[str, set[str]] = {
    "show_camera": {
        "duration_seconds",
        "enter_pip",
        "snapshot_fallback",
        "stream_type",
        "title",
        "message",
        "position",
        "title_color",
        "title_size",
        "message_color",
        "message_size",
        "background_color",
        "width",
        "height",
    },
    "show_snapshot": {
        "duration_seconds",
        "enter_pip",
        "title",
        "message",
        "position",
        "title_color",
        "title_size",
        "message_color",
        "message_size",
        "background_color",
        "width",
        "height",
    },
    "show_notification": {
        "title",
        "message",
        "duration_seconds",
        "enter_pip",
        "position",
        "title_color",
        "title_size",
        "message_color",
        "message_size",
        "background_color",
        "width",
        "height",
    },
}

NO_EXAMPLE_FIELDS: dict[str, set[str]] = {
    "show_camera": {
        "receiver_device_id",
        "camera_entity",
        "snapshot_camera_entity",
    },
    "show_snapshot": {
        "receiver_device_id",
        "camera_entity",
    },
    "show_notification": {
        "receiver_device_id",
    },
}


def test_service_fields_include_useful_examples() -> None:
    metadata = _read_service_field_examples()

    for service, fields in SERVICE_EXAMPLES.items():
        for field in fields:
            assert metadata[service][field] is not None


def test_device_and_entity_selectors_do_not_need_examples() -> None:
    metadata = _read_service_field_examples()

    for service, fields in NO_EXAMPLE_FIELDS.items():
        for field in fields:
            assert metadata[service][field] is None


def _read_service_field_examples() -> dict[str, dict[str, str | None]]:
    current_service: str | None = None
    current_field: str | None = None
    metadata: dict[str, dict[str, str | None]] = {}

    for line in SERVICES_YAML.read_text(encoding="utf-8").splitlines():
        if service := _top_level_key(line):
            current_service = service
            current_field = None
            metadata[current_service] = {}
            continue

        if current_service is None:
            continue

        if field := _field_key(line):
            current_field = field
            metadata[current_service][current_field] = None
            continue

        if current_field is not None and line.startswith("      example:"):
            metadata[current_service][current_field] = line.split(
                "example:",
                1,
            )[1].strip()

    return metadata


def _top_level_key(line: str) -> str | None:
    if line and not line.startswith(" ") and line.endswith(":"):
        return line[:-1]
    return None


def _field_key(line: str) -> str | None:
    if line.startswith("    ") and not line.startswith("      ") and line.endswith(":"):
        return line.strip()[:-1]
    return None
