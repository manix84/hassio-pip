# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/hassio-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/hassio-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/release.yml)

This directory is a placeholder for a future Home Assistant custom integration 🚧

The integration is not implemented in Phase 1. Future work is expected to add discovery 🔎, pairing 🤝, config flow support 🧭, and a `ha_tv_pip.show_camera` service 📹 for displaying camera feeds on paired Android TV or Google TV devices.

## Quality Checks ✅

From the monorepo root:

```sh
npm run install:all
npm run ha:lint
npm run ha:typecheck
npm run ha:test
npm run ha:build:dry-run
```

The placeholder package uses Ruff for Python linting, MyPy for type checking, and pytest for tests. `npm run install:all` installs those tools into `ha-integration/.venv/`.
The dry-run build packages the placeholder custom integration zip and will remain the integration build check until a fuller Home Assistant implementation exists.
