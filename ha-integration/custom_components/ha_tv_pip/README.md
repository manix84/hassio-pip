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

## Service MVP 📹

```yaml
service: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
```

The service resolves an HLS stream URL through Home Assistant's camera stream API and sends it to the paired receiver with the stored bearer token.
