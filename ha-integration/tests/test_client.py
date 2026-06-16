"""Tests for the HA TV PiP receiver client helpers."""

from custom_components.ha_tv_pip.client import (
    ShowCameraCommand,
    _error_message,
    _post_json,
)


def test_error_message_extracts_receiver_error() -> None:
    assert _error_message('{"error":"invalid_code"}') == "invalid_code"


def test_error_message_ignores_invalid_json() -> None:
    assert _error_message("not json") is None


def test_post_json_sets_bearer_token(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured = {}

    class FakeResponse:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            return None

        def read(self) -> bytes:
            return b'{"accepted":true}'

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["authorization"] = request.headers.get("Authorization")
        captured["body"] = request.data.decode()
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("custom_components.ha_tv_pip.client.urlopen", fake_urlopen)

    response = _post_json(
        "10.0.0.236",
        8765,
        "/show",
        {
            "title": "Front Door",
            "url": "https://example.test/stream.m3u8",
            "streamType": "hls",
            "previewUrl": "https://example.test/snapshot.jpg",
        },
        "secret-token",
    )

    assert response == {"accepted": True}
    assert captured["authorization"] == "Bearer secret-token"
    assert captured["timeout"] == 5
    assert '"previewUrl": "https://example.test/snapshot.jpg"' in captured["body"]


def test_post_json_sends_snapshot_stream_type(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured = {}

    class FakeResponse:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            return None

        def read(self) -> bytes:
            return b'{"accepted":true}'

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["body"] = request.data.decode()
        return FakeResponse()

    monkeypatch.setattr("custom_components.ha_tv_pip.client.urlopen", fake_urlopen)

    _post_json(
        "10.0.0.236",
        8765,
        "/show",
        {
            "title": "Front Door",
            "url": "https://example.test/snapshot.jpg",
            "streamType": "snapshot",
        },
        "secret-token",
    )

    assert '"streamType": "snapshot"' in captured["body"]


def test_show_camera_command_shape() -> None:
    command = ShowCameraCommand(
        title="Front Door",
        url="https://example.test/stream.m3u8",
        duration_seconds=30,
        enter_pip=True,
        preview_url="https://example.test/snapshot.jpg",
    )

    assert command.title == "Front Door"
    assert command.stream_type == "hls"
    assert command.preview_url == "https://example.test/snapshot.jpg"
