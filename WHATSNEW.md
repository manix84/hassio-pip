# What's New ✨

## 0.7.0 - Stage 3 Discovery Begins 🔎

Stage 3 starts with Android-side local network discovery advertising.

- Added Android NSD / mDNS advertisement for `_ha-tv-pip._tcp.local.` 📡
- Added discovery metadata for device id, receiver name, app version, pairing state, and API version 🪪
- Added discovery state to `GET /status` responses 🩺
- Added discovery status to the Android TV main screen 📺
- Added unit coverage for discovery descriptors and runtime state 🧪
- Kept Home Assistant Zeroconf discovery, config flows, pairing, and authentication out of scope for this slice 🔒

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
