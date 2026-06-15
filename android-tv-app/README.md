# HA TV PiP Receiver Android TV App 📺

[![Android TV App Quality 📺](https://github.com/manix84/hassio-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/quality-android-tv-app.yml) [![Release 📦](https://github.com/manix84/hassio-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/hassio-pip/actions/workflows/release.yml)

Phase 1 Android TV MVP for HA TV PiP. This app plays a public HLS test stream and validates Android TV Picture-in-Picture behavior where supported, with a floating overlay fallback for devices that do not expose native PiP.

Phase 2 adds the local HTTP control endpoint for developer testing.

Stage 3 adds Android-side mDNS discovery advertising so the future Home Assistant integration can find the receiver on the LAN.

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
npm run android:test
npm run android:build:dry-run
```

Android lint uses the Android Gradle plugin. Type checking compiles the debug Kotlin sources.
Unit tests run on the JVM with Gradle's debug unit test task.
The dry-run build assembles the debug APK.

## Run 🚀

1. Launch the app on an Android TV target.
2. Select `Play Test Video`.
3. Confirm the public HLS stream starts playing.
4. Select `Enter PiP` to manually enter Picture-in-Picture, or `Show Overlay` if the device uses the fallback path.

## Android TV Testing 🎮

Use a TV remote, emulator D-pad, or keyboard arrows to navigate. The main screen focuses the playback button by default.

## PiP and Overlay Testing 🪟

- While playback is running, select `Enter PiP` or `Show Overlay` ✅
- While playback is running full screen, press Home and confirm playback continues in PiP or the overlay fallback 🏠
- Reopen the app from the launcher or recents and confirm it returns to full-screen playback 🔁
- Press Back from full screen and confirm playback stops cleanly 🛑

Some Google TV devices, including Chromecast HD test hardware, do not expose Android's native PiP feature to third-party TV apps. On those devices the app can use the `SYSTEM_ALERT_WINDOW` overlay permission as a no-ADB fallback. Use `Open Overlay Settings` from the main screen, grant the permission, then test `Show Overlay`.

## Local Control Testing 🌐

The app starts a local HTTP server on port `8765` while the receiver service is running.
The main screen shows the current LAN endpoint address when Android exposes a local IPv4 address.
It also shows live control diagnostics including service state, uptime, request count, and the previous request.

```sh
curl http://ANDROID_TV_IP:8765/
curl http://ANDROID_TV_IP:8765/status
curl -X POST http://ANDROID_TV_IP:8765/close
```

Show the default public test stream:

```sh
curl -X POST http://ANDROID_TV_IP:8765/show \
  -H 'Content-Type: application/json' \
  -d '{"title":"Front Door","url":"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8","streamType":"hls","durationSeconds":30,"enterPip":true}'
```

Stage 2 does not include pairing or authentication yet. Test this only on a trusted local network.

Duplicate `/show` requests replace the current playback or overlay. `durationSeconds` is enforced for both full-screen playback and the overlay fallback.
`/status` also reports endpoint diagnostics, including control uptime, request count, and the previous request.
`/close` reports whether a display was active and which display mode it closed.
`GET /` returns API metadata and the supported endpoint list. Known endpoints return `405 Method Not Allowed` when called with the wrong HTTP method.

## Discovery Testing 🔎

When the local control service is running, the app advertises:

```txt
_ha-tv-pip._tcp.local.
```

The advertisement includes the stable device id, device name, app version, pairing state, and API version. The main screen and `/status` response show whether discovery is currently advertising.

## Stream Configuration 🎬

The test stream URL is defined in `PlayerActivity.TEST_STREAM_URL`.

## Future Notes 🚧

This app does not yet implement Home Assistant integration, pairing, authentication, camera support, snapshots, HLS from Home Assistant, or WebRTC.
