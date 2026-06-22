# HA TV PiP 📺🪟

![GitHub package.json version](https://img.shields.io/github/package-json/v/manix84/ha-tv-pip) ![GitHub License](https://img.shields.io/github/license/manix84/ha-tv-pip)

[![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml) [![Website Deploy 🌍](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml)

[![Android TV App Quality 📺](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml) [![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Website Quality 🌐](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml)

HA TV PiP is a local-first Home Assistant companion project for showing short-lived camera feeds on Android TV and Google TV devices using Android Picture-in-Picture or a local overlay fallback.

## Install HA TV PiP 🚀

HA TV PiP needs two installed parts:

1. The Android TV receiver app on each Android TV / Google TV device.
2. The Home Assistant integration in your Home Assistant instance.

### 1. Install the Android TV App 📺

1. Open the latest [GitHub Release](https://github.com/manix84/ha-tv-pip/releases).
2. Download the matching Android APK for your release version.
3. For normal installs, use `ha-tv-pip-android-release-vX.Y.Z.apk`.
4. Use `ha-tv-pip-android-debug-vX.Y.Z.apk` only when debugging or when a maintainer specifically asks for a debug build.
5. Sideload the APK onto the Android TV / Google TV receiver.
6. Open HA TV PiP on the TV once and confirm the receiver dashboard shows the local endpoint as running.

The Android app is not on the Play Store yet. Signed APKs are available through GitHub Releases; Play Store distribution and listing assets are planned.

### 2. Install the Home Assistant Integration 🏠

Until HA TV PiP is accepted as a default HACS repository:

1. Open Home Assistant.
2. Go to HACS > Custom repositories.
3. Add `https://github.com/manix84/ha-tv-pip`.
4. Select category `Integration`.
5. Install HA TV PiP.
6. Restart Home Assistant.

The HACS package installs only `custom_components/ha_tv_pip/`. The rest of this repository is for the Android app, website, docs, release tooling, and future platform work.

Use `v1.27.9` or newer for HACS installs. Earlier HACS beta builds installed and paired, but the integration Configuration screen could fail with a Home Assistant `500` error because its options dropdown schema was not frontend-serializable.

### 3. Pair the Receiver 🔐

1. In Home Assistant, open Settings > Devices & services.
2. Use the discovered HA TV PiP receiver card where possible.
3. Select Add.
4. Enter the six-digit pairing code shown on the TV.
5. Use the receiver device's Test PiP button to confirm control works.

To update a beta install, install the newer integration release in HACS, restart Home Assistant, then update or sideload the matching Android receiver APK on each TV. Matching receiver and integration versions make diagnostics and compatibility checks easier to interpret.

For integration-specific usage notes, see [`custom_components/ha_tv_pip/README.md`](custom_components/ha_tv_pip/README.md).

## Current Phase 🚦

Post-1.0 compatibility polish is active. Current work focuses on camera stream compatibility, easier troubleshooting, per-camera defaults, and clearer diagnostics across the Android TV receiver and Home Assistant integration.

The latest receiver/integration flow includes:

- Receiver-level Home Assistant defaults for preferred stream strategy, duration, popup position, snapshot fallback, width, and height.
- Per-camera defaults through `ha_tv_pip.calibrate_camera`, `ha_tv_pip.test_camera_stream`, `ha_tv_pip.set_camera_defaults`, and `ha_tv_pip.clear_camera_defaults`.
- Compatibility tests that check HLS, MJPEG, and snapshot availability for a camera/receiver pair.
- `recommended_defaults` previews so users can inspect exactly what would be saved before applying defaults.
- Optional `restream_url` and `restream_provider` per-camera defaults for users who already expose a TV-safe go2rtc or similar HLS/MJPEG stream.
- `ha_tv_pip.save_restream_source` for saving a tested go2rtc or similar restream URL as the camera's TV-safe live source.
- Saved Camera Defaults receiver sensor so saved per-camera defaults and restream source state are visible without exposing stream URLs.
- `ha_tv_pip.clear_all_camera_defaults` for resetting saved compatibility choices on a receiver before recalibrating.
- `ha_tv_pip.suggest_restream_source` for candidate manual restream stream names, go2rtc-style HLS/MJPEG URL patterns, and save-action payloads.
- Optional restream base URL support for generating candidate URLs against a real go2rtc host.
- Automatic `restream_source_suggestion` guidance in compatibility and calibration results when restreaming is recommended.
- `restreaming_recommended`, `restreaming_reason`, `restreaming_next_step`, and `restreaming_options` fields when a camera likely needs a TV-safe restreamed source.
- Manual go2rtc helper metadata in calibration/action-plan responses, including example URL patterns and the `set_camera_defaults` fields to save a working TV-safe restream URL.
- `Last Camera Compatibility`, `Camera Restreaming Recommended`, `Last Camera Result`, and `Last Command Result` entities on the receiver device.
- Receiver/integration compatibility checks for current, degraded, legacy, and incompatible receiver states, exposed through a dedicated Receiver Compatibility sensor, update guidance, and status attributes.
- Receiver service health diagnostics for foreground service state, start count, boot/package-replaced startup activity, and last service start reason.
- Redacted diagnostics for camera results, per-camera defaults, receiver status, service health, compatibility, and planned restreaming provider support.
- Restreaming provider metadata that points users toward today's TV-safe stream workarounds before future go2rtc, WebRTC, or transcoding support exists.

See [camera compatibility](docs/camera-compatibility.md) for the current HLS/MJPEG/snapshot workflow, what a TV-safe stream source means, and how future restreaming providers are expected to fit in.

<details>
<summary>Completed phase history ✅</summary>

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

</details>

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
- Local LAN control is preferred by default.
- Prefer Remote Transport can be enabled per receiver when the WebSocket path should be tried first.
- The non-preferred path remains available as the fallback path when possible.
- Test PiP, Close PiP, Refresh Status, and receiver status polling follow the same transport preference, so remote receiver mode can be tested and monitored without relying on camera entities.

Remote mode is for sending notifications to an external TV. It does not make HA TV PiP a cloud service and does not require port forwarding to the TV.

## Translation Plan 🌍

Translation support exists across the Android TV app, Home Assistant integration, and website. Phase 10 moved the main Android receiver UI, player, notification, setup, and troubleshooting strings into resources, added Tier 1 Android and Home Assistant translation files, and added Tier 1 website locale routes with localized TypeScript content modules.

English is the source language. Tier 1 translation targets are German, Dutch, French, Spanish, Italian, Brazilian Portuguese, and Polish, and are complete for the current app, integration, and website surfaces. Tier 2 and Tier 3 languages are planned after the Post-v1.0 compatibility surfaces settle and broader testing is available.

See `docs/translations.md` for the full language plan.

## Releases 📦

GitHub Releases are the distribution target for now. When code is pushed or merged into `main`, the release workflow reads the version from the root `package.json`, builds the Android TV APK, packages the Home Assistant integration, validates the APK and zip asset layout, creates draft release `vX.Y.Z` with the assets already attached, and then publishes it:

```txt
ha-tv-pip-android-debug-vX.Y.Z.apk
ha-tv-pip-android-release-vX.Y.Z.apk
ha-tv-pip-integration-vX.Y.Z.zip
ha-tv-pip-integration.zip
```

The release APK is the recommended sideload artifact for normal users. The debug APK remains available for troubleshooting and development. The stable `ha-tv-pip-integration.zip` asset is for HACS. That zip contains the integration files at archive root because HACS extracts `zip_release` assets directly into `config/custom_components/ha_tv_pip/`.

Published GitHub Releases are treated as immutable. If a release for the current version already exists, bump the root `package.json` version before producing another release.

Play Store deployment is not implemented yet. Release-prep notes for listing copy, privacy wording, screenshots, signing, and release notes live in `docs/play-store.md`.

Beta install/update validation for `1.27.0` confirmed:

- Local debug APK build produces `ha-tv-pip-android-debug-v1.27.0.apk`.
- Local signed release APK build produces `ha-tv-pip-android-release-v1.27.0.apk` when signing secrets are configured.
- Integration packaging produces both `ha-tv-pip-integration-v1.27.0.zip` and `ha-tv-pip-integration.zip`.
- The stable HACS zip contains `manifest.json`, `__init__.py`, `brand/`, translations, and other integration files at archive root so HACS installs them into `config/custom_components/ha_tv_pip/`.

## Beta Readiness 🧪

HA TV PiP is usable as beta software, but it should still be treated as a fast-moving local receiver project rather than a finished app-store product.

Before reporting a bug or testing a new release:

- Install matching Android receiver and Home Assistant integration versions.
- Confirm the Android receiver app opens and reports the local endpoint as running.
- Pair through the discovered Home Assistant receiver card where possible.
- Use the receiver device's Test PiP button to verify basic control.
- Run `ha_tv_pip.calibrate_camera` for camera-specific stream issues before changing automations.
- Download Home Assistant config entry diagnostics when opening an issue.

For common setup, pairing, camera, launcher, and remote receiver issues, see [Troubleshooting](docs/troubleshooting.md).

## Home Assistant Integration Plan 🏠

Available now:

- Home Assistant service: `ha_tv_pip.show_camera` 📹
- Home Assistant service: `ha_tv_pip.show_snapshot` 🖼️
- Home Assistant service: `ha_tv_pip.show_notification` 🔔
- Home Assistant HLS stream resolution with snapshot fallback 🎬
- Camera compatibility testing and per-camera stream defaults 🧭
- Camera calibration action plans that suggest the next service call and safe payload 🧰
- Restreaming guidance when a camera needs a TV-safe source 🧵
- Manual restream URL defaults for go2rtc or similar TV-safe HLS/MJPEG sources 🎬
- Zeroconf discovery and TV-visible pairing 🔎
- Discovery repair for DHCP address changes using the receiver's stable discovery id 📡
- Receiver status, PiP controls, launcher controls, and diagnostics 🧰
- Restreaming provider status visibility for planned go2rtc, WebRTC, and transcoding support 🩺
- Restreaming provider metadata in compatibility responses so dashboards and support notes can show current workaround paths 🔎
- Optional remote receiver mode through the user's own Home Assistant external URL 🌍
- HACS custom-repository installation using the stable release zip 🧩

Future roadmap:

- Better camera stream compatibility through automatic stream profile selection, richer go2rtc helpers, WebRTC support, and optional transcoding paths 🧵
- More notification styling options inspired by existing TV popup tools, including title/message styling, media sizing, and corner placement polish 🔔
- Default HACS repository inclusion so HA TV PiP can be installed without adding a custom repository 🧩
- Long-term official Home Assistant integration track, including config-flow polish, repairs, diagnostics, translations, tests, and architecture review readiness 🏠
- Play Store distribution for the Android TV app, including signing, listing materials, screenshots, privacy wording, and tester guidance 📺
- Receiver management improvements, including hiding the launcher icon safely while keeping receiver control available after TV restarts 🕹️
- Fire TV / Vega OS receiver support so HA TV PiP is not limited to Android TV and Google TV devices 🔥
- Exploratory Apple TV support, likely as a separate receiver design because tvOS has different background, PiP, and distribution constraints 🍎
- Broader localization beyond Tier 1 languages, with native-speaker review before wide public release 🌍

Device support plan:

- ✅ Primary: Android TV and Google TV are the current supported receiver targets 📺
- ⏭️ Next likely: Fire TV and Vega OS, because they are closest to the Android receiver model 🔥
- 🔬 Research: Samsung Tizen, LG webOS, Roku, and Apple TV / tvOS, because each may need a separate receiver design around its own app, PiP, overlay, local-network, and background-execution rules 🔬
- 👀 Watchlist: VIDAA, TiVo OS / Xperi TV OS, and operator TV platforms, to revisit if a clear distribution path and useful receiver capability model emerges 👀

## Development 🛠️

This repository is a monorepo that contains the receiver app, Home Assistant integration, and promotional website:

- `android-tv-app/`: Android TV Kotlin app 📱
- `custom_components/ha_tv_pip/`: Home Assistant custom integration 🏠
- `ha-integration/`: Integration tests and Python tooling 🧪
- `brand/`: HACS repository presentation assets 🎨
- `website/`: Vite promotional website 🌐
- `docs/`: Architecture, roadmap, and development notes 📚
- `examples/`: Example Home Assistant automations ⚙️

### Monorepo Layout 🧱

```txt
ha-tv-pip/
├── android-tv-app/
│   └── Android TV Kotlin app
├── custom_components/
│   └── ha_tv_pip/
├── ha-integration/
│   └── tests and Python tooling
├── brand/
│   └── HACS repository presentation assets
├── website/
│   └── Vite React promotional website
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── development.md
│   ├── home-assistant-official-readiness.md
│   ├── play-store.md
│   ├── troubleshooting.md
│   └── translations.md
├── examples/
│   └── home-assistant-automations/
├── README.md
├── LICENSE
└── .gitignore
```

### Run the Android TV App from Source 🚀

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

### Website Development 🌐

The promotional website lives in `website/`. It is a static Vite + React + TypeScript site for GitHub Pages, project docs entry points, and future release / Play Store / HACS links.

Run it locally:

```sh
npm run website:dev
```

### Useful Repo Scripts 🧰

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
