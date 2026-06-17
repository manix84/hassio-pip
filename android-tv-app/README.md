# HA TV PiP Receiver Android TV App 📺

[![Android TV App Quality 📺](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

Phase 1 Android TV MVP for HA TV PiP. This app plays a public HLS test stream and validates Android TV Picture-in-Picture behavior where supported, with a floating overlay fallback for devices that do not expose native PiP.

Phase 2 adds the local HTTP control endpoint for developer testing.

Stage 3 adds Android-side mDNS discovery advertising so the Home Assistant integration can find the receiver on the LAN.

Stage 4 adds local pairing and bearer-token authentication for remote `/show` and `/close` commands.

Stage 8 adds receiver management support so Home Assistant can reopen the receiver UI, hide or restore the TV launcher icon, and keep the local control service available after boot or package replacement.

Phase 9 adds optional remote receiver mode. The app can connect outbound to the user's own Home Assistant WebSocket API so external TVs can receive PiP commands without router port forwarding.

Phase 10 continues the Android TV polish pass. The main screen is now a TV-first dashboard with primary PiP controls near the top, receiver status cards, launcher controls, remote receiver status, and lower-priority diagnostics separated from everyday actions. Onboarding, pairing, and troubleshooting are intentionally handled as dashboard sections for now instead of separate screens, keeping the app simple to navigate with a TV remote. Active pairing requests also show a prominent TV-side pairing popup.

Stage 12 focuses on beta release hardening. Android work should prioritize reliable debug/release APK builds, install instructions, release artifact verification, and avoiding new receiver features until the beta release path is proven.

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
npm run android:bundle:release
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
The release bundle command builds the unsigned `.aab` used for future Play Store prep.

## Run 🚀

1. Launch the app on an Android TV target.
2. Select `Play Test Video`.
3. Confirm the public HLS stream starts playing.
4. Select `Enter PiP` to manually enter Picture-in-Picture, or `Show Overlay` if the device uses the fallback path.

## Android TV Testing 🎮

Use a TV remote, emulator D-pad, or keyboard arrows to navigate. The main screen focuses the playback button by default.

During the Phase 10 polish pass, also confirm:

- `Play Test Video` has initial focus when the screen opens 🎯
- PiP controls are visible without needing to scroll past diagnostics 📺
- Summary cards are readable from a TV viewing distance 🧭
- D-pad navigation can reach pairing, launcher, remote receiver, and diagnostics controls 🎮
- Focusing controls no longer drags the screen past important status text 🧪
- Remote receiver manual URL/token fields stay hidden until advanced setup is opened 🔐
- `Reset Pairing` and `Clear Remote` show warning confirmations before they make changes ⚠️

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
  -H 'Authorization: Bearer TOKEN' \
  -d '{"title":"Front Door","url":"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8","streamType":"hls","durationSeconds":30,"enterPip":true}'
```

Stage 4 requires pairing before `/show` and `/close`. Start pairing from Home Assistant or call `/pair/start`; the pairing code is shown on the TV only and is not returned over HTTP.
During an active pairing request, the app shows a TV-side pairing popup with the code. If the popup is dismissed, the same code remains visible in the Pairing dashboard section until it expires or pairing completes.

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

## Pairing Testing 🔐

Start pairing:

```sh
curl -X POST http://ANDROID_TV_IP:8765/pair/start \
  -H 'Content-Type: application/json' \
  -d '{"clientId":"home-assistant-dev","clientName":"Home Assistant Dev"}'
```

Enter the TV-visible code:

```sh
curl -X POST http://ANDROID_TV_IP:8765/pair/confirm \
  -H 'Content-Type: application/json' \
  -d '{"clientId":"home-assistant-dev","clientName":"Home Assistant Dev","code":"123456"}'
```

Use the returned token as `Authorization: Bearer TOKEN` for `/show` and `/close`.

## Receiver Management Testing 🧰

Paired Home Assistant instances can open the receiver UI and hide or restore the launcher icon through authenticated management endpoints.

```sh
curl -X POST http://ANDROID_TV_IP:8765/management/open \
  -H 'Authorization: Bearer TOKEN'

curl -X POST http://ANDROID_TV_IP:8765/management/launcher \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TOKEN' \
  -d '{"visible":false}'
```

If the launcher icon is hidden, recover access with Home Assistant's Open Launcher control or Android Settings > Apps > HA TV PiP.

## Remote Receiver Testing 🌍

Remote receiver mode is optional and local-first remains the default.

Preferred setup:

1. Pair the receiver with Home Assistant locally first.
2. Enter the Home Assistant external URL and long-lived access token in the integration options flow.
3. Use the Home Assistant `Sync Remote Config` button on the receiver device.
4. Confirm the Android TV Remote receiver section says the details are saved.
5. Confirm the remote state changes to `connected`.
6. Trigger `ha_tv_pip.show_camera` or `ha_tv_pip.show_snapshot` from Home Assistant.

The receiver connects outbound to the user's own Home Assistant instance. HA TV PiP does not provide or depend on a hosted cloud relay.

Manual URL and token entry remains available from `Advanced Manual Setup` on the TV for troubleshooting, but it is no longer the normal setup path.

## Translations 🌍

English is the source language.

User-facing Compose strings live in Android string resources under `app/src/main/res/values/strings.xml`, with Tier 1 translation files for German, Dutch, French, Spanish, Italian, Brazilian Portuguese, and Polish. See `../docs/translations.md`.

## Stream Configuration 🎬

The test stream URL is defined in `PlayerActivity.TEST_STREAM_URL`.

## Future Notes 🚧

This app does not yet implement WebRTC, Play Store distribution, or production signing automation.
