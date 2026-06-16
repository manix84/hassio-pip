# HA TV PiP 📺🪟

[![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml) [![Website Deploy 🌍](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml) ![GitHub License](https://img.shields.io/github/license/manix84/ha-tv-pip) ![GitHub package.json version](https://img.shields.io/github/package-json/v/manix84/ha-tv-pip)

[![Android TV App Quality 📺](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml) [![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Website Quality 🌐](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml)

HA TV PiP is a local-first Home Assistant companion project for showing short-lived camera feeds on Android TV and Google TV devices using Android Picture-in-Picture or a local overlay fallback.

This repository is a monorepo that contains the receiver app, Home Assistant integration, and promotional website:

- `android-tv-app/`: Android TV Kotlin app 📱
- `ha-integration/`: Home Assistant custom integration 🏠
- `website/`: Vite promotional website 🌐
- `docs/`: Architecture, roadmap, and development notes 📚
- `examples/`: Example Home Assistant automations ⚙️

## Current Phase 🚦

Phase 1 is complete in `0.4.0`. The Android TV MVP proves that an Android TV app can play a public HLS test stream and show it outside the full-screen app using native Picture-in-Picture where Android TV exposes it, or a no-ADB overlay fallback where native PiP is unavailable.

Phase 2 is complete in `0.6.0`. The Android TV app now includes a local HTTP control endpoint for developer testing, including status, show, close, API metadata, and clear error responses.

Stage 3 is complete in `0.14.1`. The Android TV app advertises the receiver on the local network with Android NSD / mDNS, and the Home Assistant integration discovers and configures receivers through Zeroconf.

Stage 4 is complete in `0.18.0`. Discovered receivers use a TV-visible pairing code and bearer-token authentication, so unpaired LAN clients cannot trigger `/show` or `/close`.

Stage 5 is complete in `0.21.0`. Home Assistant automations can call `ha_tv_pip.show_camera` for paired receivers, with Android TV overlay playback verified using a compatible camera stream. Some high-resolution or non-H.264 camera streams may still need future stream selection or transcoding support when their codec/profile is not Android TV-compatible.

Stage 6 is complete in `0.23.0`. Home Assistant automations can call `ha_tv_pip.show_snapshot` to display fast camera snapshots on paired receivers using the same local auth and targeting path. Video stream commands can also send an optional entity-based snapshot preview while live playback loads.

Stage 7 is complete in `0.24.0`. `ha_tv_pip.show_camera` supports `stream_type: auto`, `stream_type: hls`, and `stream_type: snapshot`, with tested receiver-side snapshot fallback when an accepted video stream fails during playback.

Stage 8 is complete in `0.26.0`. Each paired receiver now exposes Home Assistant status, connected, test, close, and launcher management entities, plus redacted config entry diagnostics for troubleshooting. Home Assistant can hide or restore the Android TV launcher icon and reopen the receiver UI without ADB.

Phase 9 is complete in `0.27.0`. Remote receiver mode lets a TV connect outbound to the user's own Home Assistant WebSocket API, so Home Assistant can send PiP commands to an external TV without router port forwarding. This is not a HA TV PiP cloud service; the Home Assistant integration remains local-first and declares `iot_class: local_push`.

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
│   ├── development.md
│   └── translations.md
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
5. Select `Play Test Video`, then use `Enter PiP`, `Show Overlay`, or press Home to test the receiver display mode.

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

## Local Control MVP 🧪

When the Android TV app is open, it starts a local HTTP control endpoint on port `8765`.

```sh
curl http://ANDROID_TV_IP:8765/status
```

Show a test HLS stream:

```sh
curl -X POST http://ANDROID_TV_IP:8765/show \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TOKEN' \
  -d '{"title":"Front Door","url":"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8","streamType":"hls","durationSeconds":30,"enterPip":true}'
```

Close playback:

```sh
curl -X POST http://ANDROID_TV_IP:8765/close \
  -H 'Authorization: Bearer TOKEN'
```

The receiver requires pairing before `/show` and `/close`. Start pairing from Home Assistant or with `POST /pair/start`; the pairing code is shown on the TV only.

## Local Discovery MVP 🔎

Stage 3 added Android-side mDNS advertising while the local endpoint is running.

```txt
Service type: _ha-tv-pip._tcp.local.
Port: 8765
Metadata: id, name, version, pairing, api
```

The receiver reports discovery state in `GET /status` and on the Android TV main screen. Home Assistant uses Zeroconf discovery as the primary setup path.

## Pairing 🔐

Pairing is intentionally a one-time two-device flow:

1. Home Assistant discovers the TV.
2. The user confirms the receiver.
3. The TV app shows a six-digit code.
4. The user enters that code in Home Assistant.
5. Home Assistant stores the returned local bearer token.

Existing pairings cannot be replaced remotely. Use `Reset Pairing` in the Android TV app before pairing a different Home Assistant instance.

## Remote Receiver Mode 🌍

Phase 9 adds optional outbound remote connectivity for travel TVs and external receivers.

- The Android TV app connects to the user's Home Assistant external URL.
- Home Assistant sends receiver commands over its existing authenticated WebSocket API.
- The receiver still proves it is paired by registering with its existing receiver pairing token.
- Local LAN control remains available and preferred when the TV is at home.

Remote mode is for sending notifications to an external TV. It does not make HA TV PiP a cloud service and does not require port forwarding to the TV.

## Translation Plan 🌍

Translation planning has started across the Android TV app, Home Assistant integration, and website, but the main translation implementation pass belongs to Phase 10 distribution polish.

English is the source language. Tier 1 translation targets are German, Dutch, French, Spanish, Italian, Brazilian Portuguese, and Polish, and should be in place before a broad release. Tier 2 and Tier 3 languages can follow after the product polish pass.

See `docs/translations.md` for the full language plan.

## Releases 📦

GitHub Releases are the distribution target for now. When a GitHub Release is published, the release workflow reads the version from the root `package.json`, builds the Android TV APK, packages the Home Assistant integration, and uploads both assets:

```txt
ha-tv-pip-android-vX.Y.Z.apk
ha-tv-pip-integration-vX.Y.Z.zip
```

Play Store deployment is not implemented yet.

## Future Home Assistant Plan 🏠

Future phases will expand the Home Assistant custom integration and Android TV receiver control features:

- Home Assistant service: `ha_tv_pip.show_camera` 📹
- Home Assistant service: `ha_tv_pip.show_snapshot` 🖼️
- HLS streams from Home Assistant 🎬
- Future WebRTC support 🧵
- HACS distribution 🧩
- Long-term official Home Assistant integration track 🏠
- Fire TV / Vega OS receiver support 🔥
- Exploratory Apple TV support 🍎
