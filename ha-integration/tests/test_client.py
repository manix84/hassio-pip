"""Tests for the HA TV PiP receiver client helpers."""

import asyncio

from custom_components.ha_tv_pip.client import (
    ShowCameraCommand,
    _error_message,
    _get_json,
    _post_json,
    async_clear_remote_configuration,
    async_close_receiver,
    async_get_receiver_status,
    async_open_receiver,
    async_set_launcher_visible,
    async_set_remote_configuration,
    show_camera_payload,
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


def test_show_camera_payload_includes_notification_style() -> None:
    payload = show_camera_payload(
        ShowCameraCommand(
            title="Enhanced notifications",
            url="",
            stream_type="notification",
            duration_seconds=15,
            enter_pip=True,
            message="Notifications can show text on the TV",
            position="bottom_right",
            title_color="#50BFF2",
            title_size=26,
            message_color="#fbf5f5",
            message_size=18,
            background_color="#0f0e0e",
        )
    )

    assert payload == {
        "title": "Enhanced notifications",
        "url": "",
        "streamType": "notification",
        "enterPip": True,
        "durationSeconds": 15,
        "message": "Notifications can show text on the TV",
        "position": "bottom_right",
        "titleColor": "#50BFF2",
        "titleSize": 26,
        "messageColor": "#fbf5f5",
        "messageSize": 18,
        "backgroundColor": "#0f0e0e",
    }


def test_get_json_fetches_receiver_status(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured = {}

    class FakeResponse:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            return None

        def read(self) -> bytes:
            return b'{"playbackState":"idle"}'

    def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("custom_components.ha_tv_pip.client.urlopen", fake_urlopen)

    response = _get_json("10.0.0.236", 8765, "/status")

    assert response == {"playbackState": "idle"}
    assert captured == {
        "url": "http://10.0.0.236:8765/status",
        "method": "GET",
        "timeout": 5,
    }


def test_async_get_receiver_status_parses_response(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        return {
            "app": "HA TV PiP Receiver",
            "version": "0.24.0",
            "deviceId": "device-1",
            "deviceName": "Nursery TV",
            "apiVersion": 1,
            "controlRunning": True,
            "playbackState": "playing",
            "displayMode": "overlay",
            "remote": {"status": "connected"},
            "management": {"launcherVisible": False},
            "pairing": {"state": "paired"},
            "lastRequest": {"method": "GET", "path": "/status", "status": 200},
            "error": "decoder_failed",
        }

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    status = asyncio.run(async_get_receiver_status("10.0.0.236", 8765))

    assert status.version == "0.24.0"
    assert status.device_id == "device-1"
    assert status.api_version == 1
    assert status.control_running is True
    assert status.playback_state == "playing"
    assert status.display_mode == "overlay"
    assert status.pairing_state == "paired"
    assert status.launcher_visible is False
    assert status.remote_status == "connected"
    assert status.error == "decoder_failed"


def test_async_close_receiver_returns_accepted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        return {"accepted": True}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    assert asyncio.run(async_close_receiver("10.0.0.236", 8765, token="token")) is True


def test_async_open_receiver_returns_accepted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        return {"accepted": True}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    assert asyncio.run(async_open_receiver("10.0.0.236", 8765, token="token")) is True


def test_async_set_launcher_visible_returns_receiver_state(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        return {"launcherVisible": False}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    assert (
        asyncio.run(
            async_set_launcher_visible(
                "10.0.0.236",
                8765,
                token="token",
                visible=False,
            )
        )
        is False
    )


def test_async_set_remote_configuration_returns_accepted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        assert args[2] == "/management/remote"
        assert args[3]["homeAssistantUrl"] == "https://example.ui.nabu.casa"
        assert args[3]["accessToken"] == "ha-token"
        return {"accepted": True}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    assert (
        asyncio.run(
            async_set_remote_configuration(
                "10.0.0.236",
                8765,
                token="pairing-token",
                home_assistant_url="https://example.ui.nabu.casa",
                access_token="ha-token",
            )
        )
        is True
    )


def test_async_clear_remote_configuration_returns_accepted(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_to_thread(func, *args):  # type: ignore[no-untyped-def]
        assert args[2] == "/management/remote"
        assert args[3] == {"clear": True}
        return {"accepted": True}

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.client.asyncio.to_thread",
        fake_to_thread,
    )

    assert (
        asyncio.run(
            async_clear_remote_configuration(
                "10.0.0.236",
                8765,
                token="pairing-token",
            )
        )
        is True
    )


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


def test_show_camera_payload_matches_receiver_wire_shape() -> None:
    command = ShowCameraCommand(
        title="Front Door",
        url="https://example.test/stream.m3u8",
        duration_seconds=30,
        enter_pip=True,
        preview_url="https://example.test/snapshot.jpg",
    )

    assert show_camera_payload(command) == {
        "title": "Front Door",
        "url": "https://example.test/stream.m3u8",
        "streamType": "hls",
        "enterPip": True,
        "durationSeconds": 30,
        "previewUrl": "https://example.test/snapshot.jpg",
    }
