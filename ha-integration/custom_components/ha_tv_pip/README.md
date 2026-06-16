# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

This directory contains the Home Assistant custom integration for HA TV PiP 🚧

Stage 3 added Zeroconf discovery support 🔎. Home Assistant can match HA TV PiP receiver advertisements and create or update a config entry from the discovered device id, host, port, receiver name, app version, pairing state, and API version.

Stage 4 added pairing 🤝 and request authentication 🔐. Setup starts pairing, asks for the six-digit code shown on the TV, stores the returned token, and keeps the token out of logs.

Stage 5 added the first control service: `ha_tv_pip.show_camera` 📹 for displaying camera feeds on paired Android TV or Google TV devices.

Stage 6 and Stage 7 added snapshot support, snapshot previews, and stream type options 🖼️.

Stage 8 added receiver entities, PiP controls, launcher controls, and diagnostics 🧰.

Phase 9 added optional remote receiver transport over the user's own Home Assistant WebSocket API 🌍.

Phase 10 adds distribution polish, Tier 1 translations, clearer docs, and preparation for HACS and longer-term official Home Assistant readiness ✨.

Distribution goals are HACS first, then long-term official Home Assistant integration readiness once the integration is mature enough. The monorepo uses root `hacs.json` with `zip_release` so HACS installs the stable `ha-tv-pip-integration.zip` release asset instead of the raw monorepo tree.

## HACS Installation 🧩

Until HA TV PiP is accepted as a default HACS repository:

1. In Home Assistant, open HACS.
2. Open Custom repositories.
3. Add `https://github.com/manix84/ha-tv-pip`.
4. Select category `Integration`.
5. Install HA TV PiP.
6. Restart Home Assistant.
7. Add the integration from Settings > Devices & services.

The HACS release zip contains `custom_components/ha_tv_pip/` at the archive root. It does not include the monorepo path `ha-integration/custom_components/ha_tv_pip/`.

## Brand Images 🎨

Home Assistant 2026.3+ reads custom integration brand images from:

```txt
custom_components/ha_tv_pip/brand/
```

This integration includes `icon.png`, `icon@2x.png`, `logo.png`, and `logo@2x.png`.

## Quality Checks ✅

From the monorepo root:

```sh
npm run install:all
npm run ha:lint
npm run ha:typecheck
npm run ha:test
npm run ha:build:dry-run
```

The integration package uses Ruff for Python linting, MyPy for type checking, and pytest for tests. `npm run install:all` installs those tools into `ha-integration/.venv/`.
The dry-run build packages the custom integration zip and will remain the integration build check until a fuller Home Assistant implementation exists.

## Receiver Entities 🩺

Each paired receiver creates:

- Status sensor with playback state and receiver diagnostics.
- Connected binary sensor based on the local `/status` endpoint.

PiP controls:

- Test PiP button that sends a known public HLS stream to the receiver.
- Close PiP button that closes the active receiver display.

Launcher controls:

- Hide Launcher switch for hiding or restoring the Android TV launcher icon.
- Open Launcher button that reopens the receiver UI from Home Assistant.

Launcher controls are marked as Home Assistant configuration entities so they are separated from day-to-day PiP controls where Home Assistant supports that grouping.

The integration also exposes config entry diagnostics with pairing tokens and active stream URLs redacted.
If the launcher icon is hidden, use the Open Launcher button or Android Settings > Apps > HA TV PiP to recover access to the receiver UI.

## Camera Service 📹

```yaml
service: ha_tv_pip.show_camera
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
  stream_type: auto
  snapshot_fallback: true
  snapshot_camera_entity: camera.front_door_sub
```

The service defaults to `stream_type: auto`, which resolves an HLS stream URL through Home Assistant's camera stream API and sends it to the paired receiver with the stored bearer token. If Home Assistant cannot produce an HLS stream in automatic mode, the integration falls back to a snapshot command. Advanced users can force `stream_type: hls` or `stream_type: snapshot`.
When `snapshot_fallback` is enabled, the integration also sends a snapshot preview so the receiver can show a still image while the video stream loads. `snapshot_camera_entity` is optional and defaults to `camera_entity`; set it when a separate camera entity provides a better still image or substream preview.
For cameras with multiple streams, use a TV-compatible H.264/HLS stream where possible. Lower-resolution secondary streams are often more reliable for TV popups than high-resolution main streams. The receiver enables Media3 decoder fallback, but unsupported camera codecs still need a compatible camera profile or future transcoding support.

## Snapshot Service 🖼️

```yaml
service: ha_tv_pip.show_snapshot
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 10
  enter_pip: true
```

The service resolves a Home Assistant camera proxy snapshot URL and sends it to the paired receiver as `streamType: snapshot`. Snapshot mode is useful for alerts where fast display is more important than live playback.

## Remote Receiver Mode 🌍

Phase 9 adds optional remote receiver transport for external TVs.

The integration registers a Home Assistant WebSocket command that a paired Android TV receiver can use after authenticating to the user's own Home Assistant instance. Once connected, `ha_tv_pip.show_camera` and `ha_tv_pip.show_snapshot` prefer the remote WebSocket transport and fall back to local HTTP if the receiver is not connected remotely.

Remote mode is not a HA TV PiP cloud service. It uses the user's Home Assistant external URL, including Nabu Casa URLs where available, and the integration remains `local_push`.

## Translations 🌍

English is the source language for the integration.

Home Assistant UI strings live in `strings.json` and `translations/*.json`. Tier 1 translation files are in place for the Phase 10 polish pass and tracked in `../../../docs/translations.md`.
