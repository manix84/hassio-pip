# HA TV PiP Receiver Android TV App 📺

[![Quality ✅](https://github.com/manix84/hassio-pip/actions/workflows/quality.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality.yml) [![Release 📦](https://github.com/manix84/hassio-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/release.yml)

Phase 1 Android TV MVP for HA TV PiP. This app plays a public HLS test stream and validates Android TV Picture-in-Picture behavior.

## Build 🛠️

Open this directory in Android Studio and let Gradle sync.

Command line:

```sh
npm run assemble
```

Requirements:

- JDK 17 or newer ☕
- Android Studio with Android SDK 36 🤖
- Android TV emulator or Android TV / Google TV device running Android 8.0/API 26 or newer 📡

From the monorepo root, the equivalent command is:

```sh
npm run android:assemble
```

## Quality Checks ✅

```sh
npm run android:lint
npm run android:typecheck
npm run android:build:dry-run
```

Android lint uses the Android Gradle plugin. Type checking compiles the debug Kotlin sources.
The dry-run build assembles the debug APK.

## Run 🚀

1. Launch the app on an Android TV target.
2. Select `Play Test Video`.
3. Confirm the public HLS stream starts playing.
4. Select `Enter PiP` to manually enter Picture-in-Picture.

## Android TV Testing 🎮

Use a TV remote, emulator D-pad, or keyboard arrows to navigate. The main screen focuses the playback button by default.

## PiP Testing 🪟

- While playback is running, select `Enter PiP` ✅
- While playback is running full screen, press Home and confirm playback continues in PiP 🏠
- Reopen the app from the launcher or recents and confirm it returns to full-screen playback 🔁
- Press Back from full screen and confirm playback stops cleanly 🛑

## Stream Configuration 🎬

The test stream URL is defined in `PlayerActivity.TEST_STREAM_URL`.

## Future Notes 🚧

This app does not yet implement Home Assistant integration, discovery, pairing, authentication, camera support, snapshots, HLS from Home Assistant, or WebRTC.
