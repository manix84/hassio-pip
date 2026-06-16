"""Tests for remote receiver provisioning helpers."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from custom_components.ha_tv_pip.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_REMOTE_ACCESS_TOKEN,
    CONF_REMOTE_HOME_ASSISTANT_URL,
    CONF_TOKEN,
)
from custom_components.ha_tv_pip.remote_setup import (
    async_sync_remote_setup,
    async_sync_remote_setup_values,
    resolved_remote_setup,
)


@dataclass
class FakeEntry:
    data: dict[str, Any]
    options: dict[str, Any] = field(default_factory=dict)


def test_resolved_remote_setup_uses_stored_options() -> None:
    entry = FakeEntry(
        data={},
        options={
            CONF_REMOTE_HOME_ASSISTANT_URL: "https://example.ui.nabu.casa",
            CONF_REMOTE_ACCESS_TOKEN: "remote-token",
        },
    )

    remote_url, remote_token = resolved_remote_setup(entry, hass=None)

    assert remote_url == "https://example.ui.nabu.casa"
    assert remote_token == "remote-token"


def test_resolved_remote_setup_falls_back_to_suggested_url(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    entry = FakeEntry(
        data={},
        options={CONF_REMOTE_ACCESS_TOKEN: "remote-token"},
    )
    monkeypatch.setattr(
        "custom_components.ha_tv_pip.remote_setup.suggested_remote_home_assistant_url",
        lambda hass: "https://suggested.example.test",
    )

    remote_url, remote_token = resolved_remote_setup(entry, hass=object())

    assert remote_url == "https://suggested.example.test"
    assert remote_token == "remote-token"


def test_async_sync_remote_setup_pushes_receiver_settings(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    entry = FakeEntry(
        data={
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "pairing-token",
        },
        options={
            CONF_REMOTE_HOME_ASSISTANT_URL: "https://example.ui.nabu.casa",
            CONF_REMOTE_ACCESS_TOKEN: "remote-token",
        },
    )

    async def fake_set_remote_configuration(
        host: str,
        port: int,
        *,
        token: str,
        home_assistant_url: str,
        access_token: str,
    ) -> bool:
        captured.update(
            {
                "host": host,
                "port": port,
                "token": token,
                "home_assistant_url": home_assistant_url,
                "access_token": access_token,
            }
        )
        return True

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.remote_setup.async_set_remote_configuration",
        fake_set_remote_configuration,
    )

    assert asyncio.run(async_sync_remote_setup(object(), entry)) is True
    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "pairing-token",
        "home_assistant_url": "https://example.ui.nabu.casa",
        "access_token": "remote-token",
    }


def test_async_sync_remote_setup_clears_receiver_settings(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: dict[str, Any] = {}
    entry = FakeEntry(
        data={
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
            CONF_TOKEN: "pairing-token",
        },
        options={},
    )

    async def fake_clear_remote_configuration(
        host: str,
        port: int,
        *,
        token: str,
    ) -> bool:
        captured.update({"host": host, "port": port, "token": token})
        return True

    monkeypatch.setattr(
        "custom_components.ha_tv_pip.remote_setup.async_clear_remote_configuration",
        fake_clear_remote_configuration,
    )

    assert asyncio.run(async_sync_remote_setup(object(), entry)) is True
    assert captured == {
        "host": "10.0.0.236",
        "port": 8765,
        "token": "pairing-token",
    }


def test_async_sync_remote_setup_values_noops_without_pairing_token() -> None:
    entry = FakeEntry(
        data={
            CONF_HOST: "10.0.0.236",
            CONF_PORT: 8765,
        }
    )

    assert (
        asyncio.run(
            async_sync_remote_setup_values(
                object(),
                entry,
                "https://example.ui.nabu.casa",
                "remote-token",
            )
        )
        is False
    )
