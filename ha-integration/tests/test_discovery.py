import pytest

from custom_components.ha_tv_pip.discovery import parse_discovery_properties


def test_parse_discovery_properties_from_android_txt_records() -> None:
    receiver = parse_discovery_properties(
        host="10.0.0.236",
        port=8765,
        properties={
            "id": b"49e3b07d8f4b7d65",
            "name": b"Nursery TV",
            "version": b"0.7.0",
            "pairing": b"disabled",
            "api": b"1",
        },
    )

    assert receiver.device_id == "49e3b07d8f4b7d65"
    assert receiver.name == "Nursery TV"
    assert receiver.host == "10.0.0.236"
    assert receiver.port == 8765
    assert receiver.version == "0.7.0"
    assert receiver.pairing == "disabled"
    assert receiver.api_version == 1


def test_parse_discovery_properties_defaults_optional_fields() -> None:
    receiver = parse_discovery_properties(
        host="10.0.0.236",
        port=None,
        properties={"id": "receiver-id"},
    )

    assert receiver.device_id == "receiver-id"
    assert receiver.name == "HA TV PiP Receiver"
    assert receiver.port == 8765
    assert receiver.version == "unknown"
    assert receiver.pairing == "disabled"
    assert receiver.api_version == 1


def test_parse_discovery_properties_requires_device_id() -> None:
    with pytest.raises(ValueError, match="id"):
        parse_discovery_properties(
            host="10.0.0.236",
            port=8765,
            properties={"name": "Nursery TV"},
        )
