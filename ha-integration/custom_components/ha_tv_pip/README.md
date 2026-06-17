# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

HA TV PiP lets Home Assistant show camera streams, snapshots, and styled notifications on Android TV and Google TV receivers 📺

Install the Android TV receiver app on each TV, then install this Home Assistant integration to discover, pair, and control those receivers from automations.

Current beta features:

- Local network discovery with Zeroconf / mDNS 🔎
- TV-visible pairing code and bearer-token authenticated control 🔐
- Camera stream, snapshot, and notification services 📹
- Receiver entities for status, connectivity, PiP controls, launcher controls, and diagnostics 🧰
- Optional remote receiver mode through your own Home Assistant external URL 🌍

HA TV PiP is still pre-release software. HACS custom-repository installation is the current integration distribution path. Play Store distribution for the Android TV app is planned; until then, install the APK from GitHub Releases.

## Before You Install 📺

You need both parts:

1. Android TV receiver app installed on the Android TV / Google TV device.
2. Home Assistant custom integration installed through HACS.

Recommended order:

1. Download the latest Android APK from the GitHub Release assets.
2. Install the APK on your Android TV / Google TV device.
3. Open the receiver app once and confirm it is running on your network.
4. Install this integration through HACS.
5. Use the discovered receiver card in Home Assistant to pair the TV.

When the app is available from the Play Store, use the Play Store install first and then add the Home Assistant integration.

## HACS Installation 🧩

Until HA TV PiP is accepted as a default HACS repository:

1. In Home Assistant, open HACS.
2. Open Custom repositories.
3. Add `https://github.com/manix84/ha-tv-pip`.
4. Select category `Integration`.
5. Install HA TV PiP.
6. Restart Home Assistant.
7. Add the integration from Settings > Devices & services.

The HACS release zip contains `custom_components/ha_tv_pip/` at the archive root. It does not include the monorepo path `ha-integration/custom_components/ha_tv_pip/`.

## Setup 🤝

After installation and Home Assistant restart:

1. Open Settings > Devices & services.
2. Wait for the discovered HA TV PiP receiver card.
3. Select Add.
4. Confirm the receiver.
5. Enter the six-digit pairing code shown on the TV.
6. Finish setup and assign the receiver to an area if desired.

Discovery is the preferred setup path. Manual setup is available as a fallback if Home Assistant and the TV are on the same network but discovery is blocked.

If the receiver was previously paired with another Home Assistant instance, open the TV app and use Reset Pairing before pairing again.

## Brand Images 🎨

Home Assistant 2026.3+ reads custom integration brand images from:

```txt
custom_components/ha_tv_pip/brand/
```

This integration includes `icon.png`, `icon@2x.png`, `logo.png`, and `logo@2x.png`.

## Quality Checks ✅

From the monorepo root:

```sh
npm run install:all
npm run ha:lint
npm run ha:typecheck
npm run ha:test
npm run ha:build:dry-run
```

The integration package uses Ruff for Python linting, MyPy for type checking, and pytest for tests. `npm run install:all` installs those tools into `ha-integration/.venv/`.
The dry-run build packages the custom integration zip and will remain the integration build check until a fuller Home Assistant implementation exists.

## Receiver Entities 🩺

Each paired receiver creates:

- Status sensor with playback state, receiver diagnostics, and parsed receiver capability metadata.
- Connected binary sensor based on the local `/status` endpoint.

PiP controls:

- Test PiP button that sends a known public HLS stream to the receiver.
- Close PiP button that closes the active receiver display.

Launcher controls:

- Hide Launcher switch for hiding or restoring the Android TV launcher icon.
- Open Launcher button that reopens the receiver UI from Home Assistant.

Launcher controls are marked as Home Assistant configuration entities so they are separated from day-to-day PiP controls where Home Assistant supports that grouping.

The integration also exposes config entry diagnostics with pairing tokens and active stream URLs redacted.
If the launcher icon is hidden, use the Open Launcher button or Android Settings > Apps > HA TV PiP to recover access to the receiver UI.

## Common Options ⚙️

Remote receiver mode:

- Configure from the integration options flow.
- Uses your own Home Assistant external URL and long-lived access token.
- The TV connects outbound to Home Assistant, so you do not need to forward ports to the TV.
- This is not a HA TV PiP cloud service.

Launcher visibility:

- Hide Launcher removes the app from compatible Android TV launcher screens.
- Open Launcher lets Home Assistant reopen the receiver UI later.
- PiP, snapshot, and notification commands do not require the user to manually open the app first after normal receiver startup behavior is available on the TV.

Diagnostics:

- Config entry diagnostics redact pairing tokens and active stream URLs.
- Use diagnostics when reporting setup, pairing, stream compatibility, or remote receiver issues.

## Camera Service 📹

```yaml
service: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
  stream_type: auto
  stream_camera_entity: camera.front_door_sub
  snapshot_fallback: true
  snapshot_camera_entity: camera.front_door_sub
  message: Someone is at the door
  position: top_right
```

The service defaults to `stream_type: auto`, which resolves an HLS stream URL through Home Assistant's camera stream API and sends it to the paired receiver with the stored bearer token. If Home Assistant cannot produce an HLS stream in automatic mode, the integration tries Home Assistant's MJPEG camera proxy stream before falling back to a snapshot command. When HLS URL resolution succeeds, automatic mode also sends an optional MJPEG fallback URL so the Android overlay can switch streams if the receiver later rejects HLS playback. Advanced users can force `stream_type: hls`, force `stream_type: mjpeg`, prefer MJPEG with fallback using `stream_type: mjpeg_first`, or force `stream_type: snapshot`.
`stream_type: mjpeg` uses Home Assistant's camera proxy stream endpoint and the receiver's overlay renderer. It is useful when a camera exposes an MJPEG stream that is more reliable on Android TV than its HLS profile. Use `stream_type: mjpeg_first` when MJPEG usually works best but HLS should still be tried before falling back to a snapshot.
`stream_camera_entity` is optional and defaults to `camera_entity`; set it when a lower-resolution, H.264, or MJPEG camera entity is more reliable for live playback on Android TV. When `snapshot_fallback` is enabled, the integration also sends a snapshot preview so the receiver can show a still image while the video stream loads. `snapshot_camera_entity` is optional and defaults to `camera_entity`; set it when a separate camera entity provides a better still image or substream preview.
`title`, `message`, and the styling fields are optional; when either `title` or `message` is present, the receiver renders the text below the camera or snapshot inside the same rounded glass popup. Width and height can be used by themselves to resize the media popup without showing a text footer.
For cameras with multiple streams, use a TV-compatible H.264/HLS stream where possible, or try `stream_type: mjpeg` when HLS is unsupported on the receiver. Lower-resolution secondary streams are often more reliable for TV popups than high-resolution main streams. The receiver enables Media3 decoder fallback, but unsupported camera codecs still need a compatible camera profile, MJPEG fallback, or future transcoding support.

## Snapshot Service 🖼️

```yaml
service: ha_tv_pip.show_snapshot
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  duration_seconds: 10
  enter_pip: true
  title: Front door
  message: Motion detected
```

The service resolves a Home Assistant camera proxy snapshot URL and sends it to the paired receiver as `streamType: snapshot`. Snapshot mode is useful for alerts where fast display is more important than live playback. Optional `title`, `message`, and styling fields can add text below the snapshot inside the same rounded popup.

## Notification Service 🔔

```yaml
service: ha_tv_pip.show_notification
target:
  device_id: living_room_tv
data:
  title: Front door
  message: Someone is at the door
  duration_seconds: 15
  position: top_right
  title_color: "#50BFF2"
  title_size: 24
  message_color: "#fbf5f5"
  message_size: 18
  background_color: "#B30F0E0E"
  width: 512
  height: 240
```

The service sends a styled text notification to the paired receiver as `streamType: notification`. It is useful for alert-style messages that do not need a camera stream or snapshot. Position values are `top_right`, `top_left`, `bottom_right`, and `bottom_left`; colors must be six-digit or alpha hex values. Optional `width` and `height` values are pixels; text-only notifications default to `512px` wide and content height, while media popups default to `640x360`. Notifications use rounded glass-style containers on the TV.

## Remote Receiver Mode 🌍

Phase 9 adds optional remote receiver transport for external TVs.

The integration registers a Home Assistant WebSocket command that a paired Android TV receiver can use after authenticating to the user's own Home Assistant instance. Once connected, `ha_tv_pip.show_camera`, `ha_tv_pip.show_snapshot`, and `ha_tv_pip.show_notification` prefer the remote WebSocket transport and fall back to local HTTP if the receiver is not connected remotely.

Remote mode is not a HA TV PiP cloud service. It uses the user's Home Assistant external URL, including Nabu Casa URLs where available, and the integration remains `local_push`.

## Known Limitations 🚧

- Some Android TV devices reject native PiP for sideloaded apps; the receiver includes an overlay fallback when permission is granted.
- High-resolution or non-H.264 camera streams may not decode on every TV device.
- Transcoding, WebRTC support, Play Store production deployment, default HACS inclusion, and official Home Assistant core submission are future goals.
- Tier 1 translations are implemented for current surfaces, but native-speaker review is still pending.

## Translations 🌍

English is the source language for the integration.

Home Assistant UI strings live in `strings.json` and `translations/*.json`. Tier 1 translation files are in place for the Phase 10 polish pass and tracked in `../../../docs/translations.md`.
