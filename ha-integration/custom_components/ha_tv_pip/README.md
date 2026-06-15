# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

This directory contains the early Home Assistant custom integration scaffold 🚧

Stage 3 begins with Zeroconf discovery support 🔎. Home Assistant can match HA TV PiP receiver advertisements and create a config entry from the discovered device id, host, port, receiver name, app version, pairing state, and API version.

The integration does not control TVs yet. Future work is expected to add pairing 🤝, request authentication 🔐, receiver status polling 📡, and a `ha_tv_pip.show_camera` service 📹 for displaying camera feeds on paired Android TV or Google TV devices.

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
