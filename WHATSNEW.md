# What's New ✨

## Unreleased - Stage 5 Service MVP 📹

- Added the first `ha_tv_pip.show_camera` service implementation 🏠
- Resolves Home Assistant camera HLS stream URLs and sends them to paired receivers 🎬
- Added service schema metadata for the Home Assistant UI 🧭
- Added focused service and receiver-client tests 🧪
- Verified the service path with a Reolink substream on Chromecast 📺
- Added receiver playback diagnostics for unsupported stream codec errors 🩺

## 0.18.0 - Stage 4 Complete 🔐

- Completed local pairing hardening for the Android TV receiver ✅
- Prevented remote clients from replacing an existing pairing without TV-side reset 🛡️
- Refreshed mDNS discovery metadata when pairing state changes 🔎
- Documented the Stage 4 pairing flow and reset process 📝
- Excluded `.DS_Store` files from packaged integration zips 📦

## 0.17.1 - Brand Icons And Pairing Polish 🎨

- Added Home Assistant custom integration brand images under `custom_components/ha_tv_pip/brand/` 🏠
- Confirmed Home Assistant shows the integration icon after restart 🧩
- Kept the direct integration `icon.png` and `logo.png` assets for compatibility 📁

## 0.17.0 - Local Receiver Pairing 🤝

- Added `/pair/start` and `/pair/confirm` endpoints to the Android TV receiver 🔐
- Showed the pairing code on the TV instead of exposing it in normal setup UX 📺
- Required bearer-token auth for `/show` and `/close` once pairing is required or complete 🛡️
- Added Home Assistant config-flow pairing and token storage 🏠
- Added a TV-side `Reset Pairing` action 🔁

## 0.14.1 - Confirmation Modal Polish 🧭

- Added a visible receiver-name field to the discovery confirmation modal so it is no longer blank 📝
- Kept the discovered receiver name as the default confirmation value 📺

## 0.14.0 - Device Page And Shared Icon 🧩

- Registered discovered receivers in Home Assistant's device registry so they have a device page 🏠
- Added explicit confirmation form schema and English translations for the discovery confirmation screen 📝
- Added a shared PNG project icon for Android, Home Assistant, and the website 🎨
- Lowered successful Zeroconf flow diagnostics back to debug logging after discovery validation 🪵

## 0.12.0 - Discovery Confirmation Flow 🔎

- Changed Zeroconf discovery to show a confirmation card instead of auto-creating entries 🧭
- Added confirmation text for discovered receivers 📝
- Kept manual host/port setup as a fallback path only 🛟

## 0.11.0 - Discovery Diagnostics 🔎

- Switched the Home Assistant Zeroconf manifest matcher to the explicit object format 🧭
- Added temporary warning-level Zeroconf flow diagnostics so HA logs show whether discovery reaches the integration 🪵
- Kept manual receiver setup as a fallback, not the primary path 🛟

## 0.10.0 - Manual Receiver Setup 🧭

- Added manual Home Assistant setup for receiver host and port 🏠
- Kept Zeroconf discovery as the preferred setup path 🔎
- Added manual setup validation and tests for fallback receiver entries 🧪

## 0.9.0 - Config Flow Load Fix 🧭

- Added a manual setup step that cleanly explains discovery-only setup 🏠
- Removed the runtime dependency on Home Assistant's Zeroconf type location 🔧
- Added config-flow helper coverage and Home Assistant strings for early abort reasons 🧪

## 0.8.1 - Home Assistant Entry Lifecycle 🧩

The Home Assistant scaffold can now load and unload discovered config entries cleanly.

- Added initial `async_setup_entry` and `async_unload_entry` lifecycle hooks 🏠
- Added async tests for config entry setup and unload behavior 🧪
- Kept receiver clients, entities, services, pairing, and authentication out of scope for this slice 🔒

## 0.8.0 - Home Assistant Discovery Scaffold 🏠

Stage 3 now has the first Home Assistant-side discovery scaffold.

- Added Home Assistant integration manifest with version sync and Zeroconf matching 🔎
- Added a config-flow entry point for HA TV PiP receiver discovery 🧭
- Added typed discovery payload parsing for receiver id, host, port, name, version, pairing state, and API version 🪪
- Added tests for Android TXT-record parsing and fallback defaults 🧪
- Confirmed the release zip now packages the integration files under `custom_components/ha_tv_pip/` 📦
- Kept TV control from Home Assistant, pairing, and authentication out of scope for this slice 🔒

## 0.7.0 - Stage 3 Discovery Begins 🔎

Stage 3 starts with Android-side local network discovery advertising.

- Added Android NSD / mDNS advertisement for `_ha-tv-pip._tcp.local.` 📡
- Added discovery metadata for device id, receiver name, app version, pairing state, and API version 🪪
- Added discovery state to `GET /status` responses 🩺
- Added discovery status to the Android TV main screen 📺
- Added unit coverage for discovery descriptors and runtime state 🧪
- Kept Home Assistant Zeroconf config flow, pairing, and authentication out of scope for this slice 🔒

## 0.6.0 - Stage 2 Endpoint Hardening 🛠️

The local control endpoint now handles the first round of real-device hardening after Chromecast validation.

- Enforced `durationSeconds` for the overlay fallback path ⏱️
- Added duplicate `/show` replacement feedback in API responses 🔁
- Added local endpoint address display on the Android TV main screen 📍
- Added `apiVersion` and `controlPort` to `/status` responses 📡
- Added endpoint uptime, request count, and previous request diagnostics to `/status` 🩺
- Added live endpoint diagnostics to the Android TV main screen 📺
- Added `GET /` API metadata plus JSON `404` and `405` error responses 🧭
- Added defensive local IP detection and endpoint display tests 🧪

## 0.5.0 - Stage 2 Local Control Begins 🌐

Stage 2 has started with a developer-testable local HTTP endpoint in the Android TV app.

- Added local receiver service on port `8765` 🛰️
- Added `GET /status` for version, device, playback, and display-mode state 📡
- Added `POST /show` for HLS playback commands 🎬
- Added `POST /close` for stopping playback and overlay fallback 🛑
- Added duplicate `/show` replacement feedback and overlay auto-close timing ⏱️
- Added the local endpoint address to the Android TV main screen 📍
- Added command validation and JVM unit tests for show requests 🧪
- Kept pairing, authentication, discovery, and Home Assistant integration out of scope for now 🔒

## 0.4.0 - Chromecast Overlay Validation 📺

Phase 1 is now validated on physical Chromecast with Google TV hardware.

- Added device compatibility detection for native PiP and overlay support 🧭
- Added a no-ADB floating overlay fallback for Google TV devices that reject native PiP 🪟
- Added an overlay permission entry point from the Android TV app UI 🔐
- Added overlay stop handling from the receiver main screen 🛑
- Updated the player action label so fallback devices show `Show Overlay` instead of `Enter PiP` 🎮
- Confirmed the fallback works on Chromecast with Google TV after granting overlay permission ✅

## 0.3.0 - Phase 1 Complete ✅

Phase 1 is now complete and validated as the Android TV PiP MVP.

- Confirmed Android TV Kotlin receiver app builds successfully 📺
- Confirmed Media3 / ExoPlayer public HLS playback path compiles cleanly 🎬
- Confirmed manual and Home-triggered PiP support is implemented 🪟
- Added Android, Home Assistant integration, and website test coverage 🧪
- Added split GitHub Actions quality jobs for linting, type checking, tests, and dry-run builds ✅
- Added native Git pre-commit checks and version bump automation 🪝
- Added local dependency installer with Android SDK detection and Home Assistant Python virtualenv setup 🛠️
- Added GitHub Pages-ready promotional website build 🌐
- Updated Android SDK/build tools configuration for Android Studio 2026.1.1 / SDK 36.1 compatibility 🤖

## 0.1.0 - Phase 1 MVP 🚀

Initial Android TV Picture-in-Picture proof of concept.

- Added Android TV Kotlin app 📺
- Added Media3 / ExoPlayer HLS playback 🎬
- Added public test stream playback 🧪
- Added manual `Enter PiP` control 🪟
- Added automatic PiP entry when Home is pressed 🏠
- Added structured Android logging 🪵
- Added root monorepo layout for future Android app and Home Assistant integration work 🧱
- Added placeholder Home Assistant integration directory 🚧
- Added package metadata and version consistency checks 📌
- Added GitHub Release packaging for Android APK and Home Assistant integration zip 📦
- Added pre-commit semantic version bump automation 🔢
- Added promotional Vite website scaffold 🌐

## Not Included Yet 🛑

- Home Assistant integration
- Camera support
- Pairing
- Discovery
- Authentication
- Cloud connectivity
- Remote access
- WebRTC
