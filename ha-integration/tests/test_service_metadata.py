from pathlib import Path

SERVICES_YAML = (
    Path(__file__).parents[2]
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
        "text_overlay",
        "width",
        "height",
        "restream_provider",
        "restream_url",
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
        "text_overlay",
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
    "test_camera_stream": {
        "save_recommendation",
        "stream_type",
        "snapshot_fallback",
        "restream_provider",
        "restream_url",
    },
    "setup_camera": {
        "check_reachability",
        "duration_seconds",
        "height",
        "position",
        "restream_base_url",
        "restream_provider",
        "restream_url",
        "save",
        "snapshot_fallback",
        "stream_type",
        "width",
    },
    "calibrate_camera": {
        "duration_seconds",
        "position",
        "save",
        "snapshot_fallback",
        "stream_type",
        "width",
        "height",
        "restream_provider",
        "restream_url",
    },
    "set_camera_defaults": {
        "stream_type",
        "duration_seconds",
        "position",
        "snapshot_fallback",
        "width",
        "height",
        "restream_provider",
        "restream_url",
    },
    "save_restream_source": {
        "stream_type",
        "duration_seconds",
        "position",
        "snapshot_fallback",
        "width",
        "height",
        "restream_provider",
        "restream_url",
    },
    "clear_camera_defaults": set(),
    "clear_all_camera_defaults": set(),
    "suggest_restream_source": {
        "restream_base_url",
        "restream_provider",
    },
    "test_restream_source": {
        "check_reachability",
        "restream_provider",
        "restream_url",
        "save",
        "snapshot_fallback",
    },
}

NO_EXAMPLE_FIELDS: dict[str, set[str]] = {
    "show_camera": {
        "camera_entity",
        "snapshot_camera_entity",
        "stream_camera_entity",
    },
    "show_snapshot": {
        "camera_entity",
    },
    "show_notification": set(),
    "test_camera_stream": {
        "camera_entity",
        "snapshot_camera_entity",
        "stream_camera_entity",
    },
    "setup_camera": {
        "camera_entity",
        "snapshot_camera_entity",
        "stream_camera_entity",
    },
    "calibrate_camera": {
        "camera_entity",
        "snapshot_camera_entity",
        "stream_camera_entity",
    },
    "set_camera_defaults": {
        "camera_entity",
        "snapshot_camera_entity",
        "stream_camera_entity",
    },
    "save_restream_source": {
        "camera_entity",
        "snapshot_camera_entity",
    },
    "clear_camera_defaults": {
        "camera_entity",
    },
    "clear_all_camera_defaults": set(),
    "suggest_restream_source": {
        "camera_entity",
    },
    "test_restream_source": {
        "camera_entity",
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


def test_services_target_only_ha_tv_pip_devices() -> None:
    content = SERVICES_YAML.read_text(encoding="utf-8")

    for service in SERVICE_EXAMPLES:
        service_block = _service_block(content, service)
        assert "  target:\n" in service_block
        assert "    device:\n" in service_block
        assert "      integration: ha_tv_pip\n" in service_block
        assert "receiver_device_id:" not in service_block


def _service_block(content: str, service: str) -> str:
    lines = content.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line == f"{service}:\n")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index] and not lines[index].startswith(" "):
            end = index
            break
    return "".join(lines[start:end])


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
