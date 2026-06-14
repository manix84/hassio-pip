# HA TV PiP 📺🪟

[![Release 📦](https://github.com/manix84/hassio-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/release.yml) [![Website Deploy 🌍](https://github.com/manix84/hassio-pip/actions/workflows/website.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/website.yml) ![GitHub License](https://img.shields.io/github/license/manix84/hassio-pip) ![GitHub package.json version](https://img.shields.io/github/package-json/v/manix84/hassio-pip)

[![Android TV App Quality 📺](https://github.com/manix84/hassio-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality-android-tv-app.yml) [![Home Assistant Integration Quality 🏠](https://github.com/manix84/hassio-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality-ha-integration.yml) [![Website Quality 🌐](https://github.com/manix84/hassio-pip/actions/workflows/quality-website.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality-website.yml)

HA TV PiP is a planned Home Assistant companion project for showing short-lived camera feeds on Android TV and Google TV devices using Android Picture-in-Picture.

This repository is a monorepo that contains the receiver app, future Home Assistant integration, and promotional website:

- `android-tv-app/`: Android TV Kotlin app 📱
- `ha-integration/`: Home Assistant custom integration 🏠
- `website/`: Vite promotional website 🌐
- `docs/`: Architecture, roadmap, and development notes 📚
- `examples/`: Example Home Assistant automations ⚙️

## Current Phase ✅

Phase 1 is complete. The Android TV MVP proves that an Android TV app can play a public HLS test stream and reliably enter and exit Picture-in-Picture mode.

The Home Assistant integration, local control endpoint, discovery, pairing, authentication, camera support, snapshots, and WebRTC support are not implemented yet.

## Monorepo Layout 🧱

```txt
ha-tv-pip/
├── android-tv-app/
│   └── Android TV Kotlin app
├── ha-integration/
│   └── custom_components/ha_tv_pip/
├── website/
│   └── Vite React promotional website
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── development.md
├── examples/
│   └── home-assistant-automations/
├── README.md
├── LICENSE
└── .gitignore
```

## Run the Android TV App 🚀

1. Open `android-tv-app/` in Android Studio.
2. Let Android Studio sync Gradle.
3. Select an Android TV or Google TV device, or create an Android TV emulator.
4. Run the `app` configuration.
5. Select `Play Test Video`, then use `Enter PiP` or press Home to test Picture-in-Picture.

From VSCode or a terminal with a configured JDK and Android SDK:

```sh
npm run install:all
npm run android:assemble
```

Useful repo scripts:

```sh
npm run check
npm run lint
npm run typecheck
npm run test
npm run android:assemble
npm run android:build:dry-run
npm run android:lint
npm run android:test
npm run android:clean
npm run ha:build:dry-run
npm run ha:test
npm run website:dev
npm run website:build
npm run website:build:dry-run
npm run website:test
```

## Website 🌐

The promotional website lives in `website/`. It is a static Vite + React + TypeScript site for GitHub Pages, project docs entry points, and future release / Play Store / HACS links.

Run it locally:

```sh
npm run website:dev
```

## Releases 📦

GitHub Releases are the distribution target for now. When a GitHub Release is published, the release workflow reads the version from the root `package.json`, builds the Android TV APK, packages the Home Assistant integration, and uploads both assets:

```txt
ha-tv-pip-android-vX.Y.Z.apk
ha-tv-pip-integration-vX.Y.Z.zip
```

Play Store deployment is not implemented yet.

## Future Home Assistant Plan 🏠

Future phases will add a Home Assistant custom integration and Android TV receiver control features:

- Local HTTP control endpoint 🌐
- mDNS discovery 🔎
- Device pairing 🤝
- Home Assistant config flow 🧭
- Home Assistant service: `ha_tv_pip.show_camera` 📹
- HLS streams from Home Assistant 🎬
- Snapshots and WebRTC support 🖼️
