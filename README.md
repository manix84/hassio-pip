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

Stage 7 is complete in `0.24.0`. `ha_tv_pip.show_camera` supports `stream_type: auto`, `stream_type: hls`, `stream_type: mjpeg`, `stream_type: mjpeg_first`, and `stream_type: snapshot`, with tested receiver-side snapshot fallback when an accepted video stream fails during playback. Current compatibility work adds optional `stream_camera_entity` support for cameras that expose a separate TV-friendly stream entity.

Stage 8 is complete in `0.26.0`. Each paired receiver now exposes Home Assistant status, connected, test, close, and launcher management entities, plus redacted config entry diagnostics for troubleshooting. Home Assistant can hide or restore the Android TV launcher icon and reopen the receiver UI without ADB.

Phase 9 is complete in `0.27.0`. Remote receiver mode lets a TV connect outbound to the user's own Home Assistant WebSocket API, so Home Assistant can send PiP commands to an external TV without router port forwarding. This is not a HA TV PiP cloud service; the Home Assistant integration remains local-first and declares `iot_class: local_push`.

Phase 10 distribution prep is complete except for actual Play Store deployment, which remains intentionally out of scope for now. The Android TV app has moved from a developer-style status page to a TV-first receiver dashboard with clear PiP controls, launcher controls, remote receiver status, and diagnostics kept out of the way of everyday actions. Remote receiver setup now prefers Home Assistant-assisted config sync, with manual URL/token entry kept as an advanced TV-side fallback. Onboarding, pairing, and troubleshooting are currently implemented as dashboard sections rather than separate screens to keep the TV app shallow and D-pad friendly.

Stage 11 is complete in `0.45.0`. HA TV PiP now supports styled text-only notifications plus camera and snapshot popups with optional title/message footers, configurable corner position, title/message colors, text sizes, translucent glass backgrounds, and overlay width/height options.

Stage 12 is complete in `0.48.0`. The beta release hardening pass validated full quality checks, release packaging, Android debug and release APK builds, HACS zip layout, website build output, public install docs, Stage 11 examples, and the first GitHub release-candidate workflow.

Post-1.0 compatibility polish now includes receiver-level Home Assistant defaults for preferred stream strategy, duration, popup position, snapshot fallback, width, and height. Individual automations can still override any of those values per action.

The current compatibility pass adds Home Assistant-side camera stream testing and per-camera defaults. Users can test HLS, MJPEG, and snapshot availability for a camera/receiver pair, then store camera-specific stream, fallback, position, duration, width, and height defaults so automations stay simpler.

Compatibility tests now flag when a camera likely needs a TV-safe restreamed source. If HLS and MJPEG are unavailable, or the receiver can only use snapshots, results include `restreaming_recommended`, `restreaming_reason`, `restreaming_next_step`, and `restreaming_options` so users know to try another camera entity, a lower-resolution profile, go2rtc, WebRTC, or future transcoding support.

See [camera compatibility](docs/camera-compatibility.md) for the current HLS/MJPEG/snapshot workflow, what a TV-safe stream source means, and how future restreaming providers are expected to fit in.

Receiver/integration compatibility checks now compare receiver API and capability metadata with the Home Assistant integration. Older receivers without capability metadata are treated as legacy best-effort, degraded receivers expose missing optional features in diagnostics, and camera popups drop optional title/message footer fields when the receiver cannot render them.

Camera troubleshooting now includes a `Last Camera Result` receiver sensor and redacted diagnostics for the latest camera or snapshot command. The result records the requested stream strategy, final stream type sent to the receiver, transport path, fallback usage, popup size, status, and failure reason where available without storing camera URLs.

`ha_tv_pip.test_camera_stream` can now save its recommended stream strategy as per-camera defaults with `save_recommendation: true`. Any explicit test fields, such as width, height, position, duration, snapshot fallback, or stream/snapshot entities, are saved with the recommendation so future automations can omit them.

Compatibility test responses include `recommended_defaults`, so users can inspect exactly what would be saved before enabling `save_recommendation`.

The receiver device also exposes a `Last Camera Compatibility` sensor so the latest compatibility test recommendation is visible without opening diagnostics.

When the latest compatibility result indicates that live video likely needs another TV-safe source, the receiver device's `Camera Restreaming Recommended` binary sensor turns on with the camera, recommendation, restreaming reason, next step, suggested options, and test timestamp in its attributes.

For a simpler setup flow, `ha_tv_pip.calibrate_camera` tests the camera, returns a friendly summary, and can save the recommended per-camera defaults in one action with `save: true`.

Stored per-camera defaults are included in Home Assistant diagnostics, making calibration state easier to review when troubleshooting.

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
│   ├── home-assistant-official-readiness.md
│   ├── play-store.md
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
npm run android:bundle:release
npm run android:lint
npm run android:test
npm run android:clean
npm run ha:build:dry-run
npm run ha:test
npm run website:dev
npm run website:build
npm run website:build:dry-run
npm run website:a11y
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

The root and status responses include receiver capabilities so clients can see supported stream command types, notification positions, preview images, playable fallbacks, overlay fallback, pairing, launcher management, and remote receiver settings. The status response also includes control, discovery, pairing, remote receiver, management, and playback diagnostics. Playback details are exposed both through the older top-level fields and a nested `playback` object containing display mode, stream type, URL, preview URL, playable fallback URL/type, error detail, and update time.

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
During an active pairing request, the TV app also shows a pairing popup with the six-digit code. If that popup is dismissed, the code remains visible in the Pairing dashboard section until the pairing session expires or completes.

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

Translation planning has started across the Android TV app, Home Assistant integration, and website. Phase 10 moved the main Android receiver UI, player, notification, setup, and troubleshooting strings into resources, added Tier 1 Android and Home Assistant translation files, and added Tier 1 website locale routes with localized TypeScript content modules.

English is the source language. Tier 1 translation targets are German, Dutch, French, Spanish, Italian, Brazilian Portuguese, and Polish, and are complete for the current app, integration, and website surfaces. Tier 2 and Tier 3 languages are planned after beta hardening and broader testing.

See `docs/translations.md` for the full language plan.

## Releases 📦

GitHub Releases are the distribution target for now. When code is pushed or merged into `main`, the release workflow reads the version from the root `package.json`, builds the Android TV APK, packages the Home Assistant integration, creates draft release `vX.Y.Z` with the assets already attached, and then publishes it:

```txt
ha-tv-pip-android-debug-vX.Y.Z.apk
ha-tv-pip-android-release-vX.Y.Z.apk
ha-tv-pip-integration-vX.Y.Z.zip
ha-tv-pip-integration.zip
```

The debug APK is for beta testing and easier sideloading. The release APK is currently unsigned and is the shape that will become the normal Android release artifact once signing is introduced. The stable `ha-tv-pip-integration.zip` asset is for HACS. That zip contains `custom_components/ha_tv_pip/` at its root so HACS-style installs do not include the monorepo wrapper path.

Published GitHub Releases are treated as immutable. If a release for the current version already exists, bump the root `package.json` version before producing another release.

Play Store deployment is not implemented yet. Release-prep notes for listing copy, privacy wording, screenshots, signing, and release notes live in `docs/play-store.md`.

## HACS Installation 🧩

Until HA TV PiP is accepted as a default HACS repository, add it as a custom repository:

1. Open Home Assistant.
2. Go to HACS > Custom repositories.
3. Add `https://github.com/manix84/ha-tv-pip`.
4. Select category `Integration`.
5. Install HA TV PiP.
6. Restart Home Assistant.
7. Add the integration from Settings > Devices & services, preferably using the discovered receiver card.

## Home Assistant Integration Plan 🏠

Available now:

- Home Assistant service: `ha_tv_pip.show_camera` 📹
- Home Assistant service: `ha_tv_pip.show_snapshot` 🖼️
- Home Assistant service: `ha_tv_pip.show_notification` 🔔
- Home Assistant HLS stream resolution with snapshot fallback 🎬
- Camera compatibility testing and per-camera stream defaults 🧭
- Restreaming guidance when a camera needs a TV-safe source 🧵
- Zeroconf discovery and TV-visible pairing 🔎
- Receiver status, PiP controls, launcher controls, and diagnostics 🧰
- Optional remote receiver mode through the user's own Home Assistant external URL 🌍
- HACS custom-repository installation using the stable release zip 🧩

Future roadmap:

- Better camera stream compatibility, including future WebRTC and/or transcoding work 🧵
- Default HACS repository inclusion 🧩
- Long-term official Home Assistant integration track 🏠
- Play Store distribution for the Android TV app 📺
- Fire TV / Vega OS receiver support 🔥
- Exploratory Apple TV support 🍎
