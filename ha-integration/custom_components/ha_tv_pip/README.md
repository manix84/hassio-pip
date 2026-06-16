# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

This directory contains the Home Assistant custom integration for HA TV PiP 🚧

Stage 3 added Zeroconf discovery support 🔎. Home Assistant can match HA TV PiP receiver advertisements and create or update a config entry from the discovered device id, host, port, receiver name, app version, pairing state, and API version.

Stage 4 added pairing 🤝 and request authentication 🔐. Setup starts pairing, asks for the six-digit code shown on the TV, stores the returned token, and keeps the token out of logs.

Stage 5 adds the first control service: `ha_tv_pip.show_camera` 📹 for displaying camera feeds on paired Android TV or Google TV devices.

Distribution goals are HACS first, then long-term official Home Assistant integration readiness once the integration is mature enough.

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

## Camera Service 📹

```yaml
service: ha_tv_pip.show_camera
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
  snapshot_fallback: true
  snapshot_camera_entity: camera.front_door_sub
```

The service resolves an HLS stream URL through Home Assistant's camera stream API and sends it to the paired receiver with the stored bearer token.
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
