# HA TV PiP Receiver Android TV App 📺

[![Android TV App Quality 📺](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-android-tv-app.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

Phase 1 Android TV MVP for HA TV PiP. This app plays a public HLS test stream and validates Android TV Picture-in-Picture behavior where supported, with a floating overlay fallback for devices that do not expose native PiP.

Phase 2 adds the local HTTP control endpoint for developer testing.

Stage 3 adds Android-side mDNS discovery advertising so the Home Assistant integration can find the receiver on the LAN.

Stage 4 adds local pairing and bearer-token authentication for remote `/show` and `/close` commands.

Stage 8 adds receiver management support so Home Assistant can reopen the receiver UI, hide or restore the TV launcher icon, and keep the local control service available after boot or package replacement.

Phase 9 adds optional remote receiver mode. The app can connect outbound to the user's own Home Assistant WebSocket API so external TVs can receive PiP commands without router port forwarding.

Phase 10 starts the Android TV polish pass. The main screen is being reshaped into a TV-first dashboard with primary PiP controls near the top, receiver status cards, launcher controls, remote receiver settings, and lower-priority diagnostics separated from everyday actions.

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

During the Phase 10 polish pass, also confirm:

- `Play Test Video` has initial focus when the screen opens 🎯
- PiP controls are visible without needing to scroll past diagnostics 📺
- Summary cards are readable from a TV viewing distance 🧭
- D-pad navigation can reach pairing, launcher, remote receiver, and diagnostics controls 🎮
- Focusing controls no longer drags the screen past important status text 🧪

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

1. Pair the receiver with Home Assistant locally first.
2. Create a Home Assistant long-lived access token for testing.
3. Open the Android TV app and enter the Home Assistant external URL.
4. Enter the long-lived access token.
5. Select `Save Remote`.
6. Confirm the remote state changes to `connected`.
7. Trigger `ha_tv_pip.show_camera` or `ha_tv_pip.show_snapshot` from Home Assistant.

The receiver connects outbound to the user's own Home Assistant instance. HA TV PiP does not provide or depend on a hosted cloud relay.

Manual token entry is an advanced fallback for now. A later Phase 10 setup pass should let Home Assistant assist or provision remote receiver settings so normal users do not need to type long URLs or tokens with a TV remote.

## Translations 🌍

English is the source language.

During the Phase 10 polish pass, user-facing Compose strings should move into Android string resources under `app/src/main/res/values/strings.xml`, with Tier 1 translations added before broad release. See `../docs/translations.md`.

## Stream Configuration 🎬

The test stream URL is defined in `PlayerActivity.TEST_STREAM_URL`.

## Future Notes 🚧

This app does not yet implement WebRTC or polished remote onboarding.
