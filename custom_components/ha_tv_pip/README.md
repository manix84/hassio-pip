# HA TV PiP Home Assistant Integration 🏠

[![Home Assistant Integration Quality 🏠](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-ha-integration.yml) [![Release 📦](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/release.yml)

HA TV PiP lets Home Assistant show camera streams, snapshots, and styled notifications on Android TV and Google TV receivers 📺

Install the Android TV receiver app on each TV, then install this Home Assistant integration to discover, pair, and control those receivers from automations.

## Install HA TV PiP 🚀

You need both parts:

1. Android TV receiver app installed on each Android TV / Google TV device.
2. Home Assistant custom integration installed through HACS.

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

1. In Home Assistant, open HACS.
2. Open Custom repositories.
3. Add `https://github.com/manix84/ha-tv-pip`.
4. Select category `Integration`.
5. Install HA TV PiP.
6. Restart Home Assistant.

The HACS release zip contains the integration files at archive root because HACS extracts the release asset directly into `config/custom_components/ha_tv_pip/`.

Use `v1.27.9` or newer for HACS installs. Earlier HACS beta builds can show `500 Internal Server Error` when opening the integration Configuration screen because Home Assistant could not serialize the old options dropdown schema.

### 3. Pair the Receiver 🔐

1. Open Settings > Devices & services.
2. Wait for the discovered HA TV PiP receiver card.
3. Select Add.
4. Confirm the receiver.
5. Enter the six-digit pairing code shown on the TV.
6. Finish setup and assign the receiver to an area if desired.

Discovery is the preferred setup path. Manual setup is available as a fallback if Home Assistant and the TV are on the same network but discovery is blocked.

If the receiver was previously paired with another Home Assistant instance, open the TV app and use Reset Pairing before pairing again.

For beta updates, update the HACS integration, restart Home Assistant, then install the matching Android receiver APK from the same GitHub Release. The receiver and integration can gracefully degrade around some missing optional features, but matching versions are the recommended support path.

The receiver Status sensor and Receiver Compatibility sensor expose `integration_version`, `receiver_version`, `version_alignment`, `versions_match`, and `version_guidance` attributes. Use those fields to confirm the HACS integration and Android APK came from the same release before debugging playback or pairing issues.

Current beta features:

- Local network discovery with Zeroconf / mDNS 🔎
- TV-visible pairing code and bearer-token authenticated control 🔐
- Camera stream, snapshot, and notification services 📹
- Camera compatibility testing and per-camera defaults 🧭
- Receiver entities for status, connectivity, PiP controls, launcher controls, and diagnostics 🧰
- Optional remote receiver mode through your own Home Assistant external URL 🌍

HA TV PiP is still pre-release software. HACS custom-repository installation is the current integration distribution path. Play Store distribution for the Android TV app is planned; until then, install the signed release APK from GitHub Releases.

## Beta Support Checklist 🧪

Before reporting a setup or playback issue:

1. Confirm the Android receiver app and this Home Assistant integration are on the same release version.
2. Confirm the Android receiver app opens and reports the local endpoint as running.
3. Use the receiver device's Test PiP button to verify basic receiver control.
4. For camera issues, run `ha_tv_pip.calibrate_camera` with `save: false` and review the recommendation.
5. Download config entry diagnostics from the integration entry. Tokens and active stream URLs are redacted, but review them before sharing.

Common setup, discovery, pairing, stream compatibility, launcher recovery, and remote receiver checks are documented in the project troubleshooting guide:

<https://github.com/manix84/ha-tv-pip/blob/main/docs/troubleshooting.md>

## Brand Images 🎨

Home Assistant 2026.3+ reads custom integration brand images from:

```txt
custom_components/ha_tv_pip/brand/
```

This integration includes `icon.png`, `icon@2x.png`, `logo.png`, and `logo@2x.png`.

The repository root also contains `brand/icon.png` and `brand/logo.png` for HACS repository presentation.

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
- Status sensor attributes for receiver service health, including foreground state, start count, last start reason, and last boot/package-replaced receiver action.
- Status sensor attributes for remote receiver health, including connection attempts, successful connections, received command messages, last disconnect reason, and connection timestamps.
- Focused sensors for active display mode, active stream type, last receiver error, receiver app version, and receiver compatibility.
- Last Camera Compatibility sensor with the latest stream test recommendation.
- Last Camera Result sensor with the latest redacted camera/snapshot command outcome.
- Last Command Result sensor with the latest receiver command status, command type, transport, stream choice, and failure reason.
- Saved Camera Defaults sensor with the number of cameras that have saved defaults, plus non-sensitive attributes showing which cameras use saved restream sources.
- Restreaming Provider Status sensor for planned, configured, and active provider visibility.
- Connected binary sensor based on the configured local/remote status transport path.
- Remote connected binary sensor for outbound remote receiver mode.

Detailed receiver, compatibility, command-result, restreaming, connectivity, and saved-defaults entities are marked as Home Assistant diagnostic entities. The main Status sensor remains the primary receiver state.

PiP controls:

- Refresh Status button that checks the receiver status endpoint on demand.
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
- The first options screen keeps everyday defaults compact; use Show advanced settings for popup position, width, height, and remote URL/token fields.
- Uses your own Home Assistant external URL and long-lived access token.
- The TV connects outbound to Home Assistant, so you do not need to forward ports to the TV.
- Local HTTP is used first by default. Prefer Remote Transport can be enabled when connected remote receivers should receive commands over the Home Assistant WebSocket path first.
- Receiver status entities add a `transport` attribute so you can see whether local HTTP or remote WebSocket supplied the latest poll.
- This is not a HA TV PiP cloud service.

Launcher visibility:

- Hide Launcher removes the app from compatible Android TV launcher screens.
- Open Launcher lets Home Assistant reopen the receiver UI later.
- PiP, snapshot, and notification commands do not require the user to manually open the app first after normal receiver startup behavior is available on the TV.

Diagnostics:

- Config entry diagnostics redact pairing tokens and active stream URLs.
- Use diagnostics when reporting setup, pairing, stream compatibility, receiver startup, or remote receiver issues.

Receiver service health:

- The status sensor includes `service_running`, `service_foreground`, `service_start_count`, `service_last_start_reason`, `service_last_started_at_millis`, `service_last_destroyed_at_millis`, `last_boot_receiver_action`, and `last_boot_receiver_at_millis`.
- After a TV restart or app update, these fields help confirm whether Android delivered the boot/package-replaced event and whether the foreground receiver service started again.

Remote receiver health:

- The status sensor and Remote Connected binary sensor include `remote_connection_attempt_count`, `remote_successful_connection_count`, `remote_message_count`, `remote_last_connection_attempt_at_millis`, `remote_connected_at_millis`, `remote_last_message_at_millis`, `remote_last_disconnected_at_millis`, `remote_last_disconnect_reason`, and `remote_last_error`.
- The configured Home Assistant external URL is not exposed in entity attributes; the integration only reports whether a remote URL is configured.

## Receiver Compatibility 🧩

The integration reads receiver `/status` API and capability metadata and computes a compatibility summary:

- `compatible`: the receiver supports the expected command and display features.
- `degraded`: the receiver works but is missing optional features such as media text footers, playable fallback, launcher management, or remote receiver settings.
- `legacy`: the receiver does not report capability metadata, so Home Assistant uses best-effort behavior.
- `incompatible`: the receiver is missing a required API version or display stream support.

Compatibility state, missing features, warnings, version alignment, and update guidance are exposed on the status and Receiver Compatibility sensor attributes and in config entry diagnostics. Camera and snapshot commands gracefully drop optional title/message footer fields when the receiver cannot render media text, while still sending the media command where possible.

## Receiver Defaults ⚙️

Each receiver has configurable defaults in the Home Assistant integration options. These defaults are used only when an action does not provide its own value:

- Preferred stream strategy: `auto`, `hls`, `mjpeg`, `mjpeg_first`, or `snapshot`.
- Default duration in seconds.
- Default popup position: `top_right`, `top_left`, `bottom_right`, or `bottom_left`.
- Snapshot fallback default for camera streams.
- Default popup width and height in pixels.

Use `0` for duration, width, or height to keep the built-in service defaults. Explicit service data always wins, so one automation can still override the receiver defaults when needed.

Per-camera defaults can be stored with `ha_tv_pip.set_camera_defaults`. They apply before receiver-level defaults, which is useful when one camera needs `mjpeg_first`, a substream entity, a different snapshot entity, or a different popup size. Use `ha_tv_pip.clear_camera_defaults` to remove stored defaults for one camera, or `ha_tv_pip.clear_all_camera_defaults` to remove every saved camera default from a receiver.

Stored per-camera defaults are visible through the receiver device's Saved Camera Defaults sensor and included in config entry diagnostics so setup issues can be reviewed without exposing stream URLs.

## Camera Defaults Workflow ⚙️

Run calibration without saving first:

```yaml
service: ha_tv_pip.calibrate_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  width: 720
  height: 405
  snapshot_fallback: true
  save: false
```

Inspect `summary`, `action_plan`, `recommendation_reason`, `restreaming_recommended`, `restreaming_reason`, `restreaming_next_step`, `restreaming_options`, and `recommended_defaults` in the action response. `action_plan` includes the suggested next HA TV PiP service, a safe payload to use, and a complete `service_call` object with `action`, `target.device_id`, and `data`.

Save the recommendation when it looks right:

```yaml
service: ha_tv_pip.calibrate_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  width: 720
  height: 405
  snapshot_fallback: true
  save: true
```

Use the camera from automations without repeating those defaults:

```yaml
service: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
```

## Camera Compatibility Test 🧭

For the normal setup workflow, use `ha_tv_pip.setup_camera`:

```yaml
service: ha_tv_pip.setup_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  stream_camera_entity: camera.front_door_sub
  snapshot_fallback: true
  width: 720
  height: 405
  save: true
```

Setup runs calibration when no `restream_url` is supplied, or validates and optionally saves a manual restream URL when one is supplied. The response includes `setup_mode`, `setup_summary`, `setup_steps`, and either the calibration/action-plan result or the restream validation result. `setup_steps` is an ordered checklist with stable keys, labels, statuses, and follow-up actions or validation details for UI helpers and troubleshooting.

The lower-level `ha_tv_pip.calibrate_camera` action remains available for troubleshooting. Calibration tests HLS, MJPEG, and snapshot availability, returns a summary with the recommended stream strategy and next step, includes an `action_plan` with the next service call to try, and can save the recommendation as per-camera defaults.

If live HLS/MJPEG paths are unavailable, the response includes `restreaming_recommended: true`, `restreaming_reason`, `restreaming_next_step`, and `restreaming_options`. This means the current camera entity is likely snapshot-only for HA TV PiP, or needs a TV-safe source such as another camera entity, a lower-resolution profile, go2rtc, WebRTC, or future transcoding support.

If you already expose a TV-safe stream through go2rtc or another local restreaming tool, set `restream_url` and `restream_provider` with `ha_tv_pip.save_restream_source`. The receiver will use that URL for live video while still using `camera_entity` for titles and snapshot previews. Saved restream URLs are redacted from diagnostics and are not exposed by the Saved Camera Defaults sensor.

Use `ha_tv_pip.suggest_restream_source` when you need help turning a camera entity into manual restream setup values. It returns candidate stream names, go2rtc/Frigate-style HLS/MJPEG URL patterns, provider help, ordered setup steps, a `test_restream_source` action payload for the first HLS candidate, a fallback MJPEG test payload, and the follow-up `save_restream_source` action payload to use after a URL has been tested. Helper payloads include both the legacy `service` key and a copyable Home Assistant `action` key.

Use `ha_tv_pip.test_restream_source` before saving a manual URL. It infers whether the candidate is HLS or MJPEG, checks that the selected receiver reports support for that stream type, optionally performs a lightweight reachability check from Home Assistant, and returns a safe `save_restream_source` payload when the URL looks worth saving.

For the full setup workflow, see the project camera compatibility guide: <https://github.com/manix84/ha-tv-pip/blob/main/docs/camera-compatibility.md>.

For lower-level troubleshooting, use `ha_tv_pip.test_camera_stream`:

```yaml
service: ha_tv_pip.test_camera_stream
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  stream_camera_entity: camera.front_door_sub
  snapshot_camera_entity: camera.front_door
  save_recommendation: true
  snapshot_fallback: true
  width: 720
  height: 405
```

The compatibility test checks whether Home Assistant can resolve HLS, MJPEG, and snapshot URLs for the selected camera and receiver. It stores a non-sensitive last result in diagnostics, including available stream types and the recommended stream type. It does not store or expose camera URLs in the compatibility result.

The result also includes `recommendation_reason`, which explains why the integration recommends `auto`, `mjpeg_first`, `hls`, `mjpeg`, or `snapshot`. For example, a receiver that supports playable fallback may prefer `auto`, while a receiver without playable fallback can recommend `mjpeg_first` when both HLS and MJPEG are available.

`restreaming_recommended` is separate from `recommended_stream_type`. A `snapshot` recommendation can be useful for fast alerts, while `snapshot_only_live_stream_restreaming_recommended` explains that a live popup probably needs a different stream source. `no_supported_stream_paths_restreaming_recommended` means Home Assistant could not resolve any supported HLS, MJPEG, or snapshot path for the selected camera/receiver pair. Use `restreaming_next_step`, `restreaming_options`, and `restreaming_provider` as stable action hints when building dashboards or troubleshooting notes.

Restreaming provider support is planned, not active. Until go2rtc, WebRTC, or transcoding support is implemented, compatibility and calibration responses include provider metadata that points to current paths: use a TV-safe `stream_camera_entity`, try `mjpeg_first`, keep snapshot fallback enabled, choose a lower-resolution or H.264 camera substream, then save the working values as per-camera defaults.

The response includes `recommended_defaults`, which previews the exact per-camera defaults that would be stored. Inspect that payload first if you want to verify the recommendation before saving it.

The response also includes `action_plan`. For compatible cameras, this points to saving recommended defaults or using `show_camera` after defaults have been saved. For snapshot-only cameras, it points to either saving snapshot alerts now or configuring a TV-safe live source with fields such as `stream_camera_entity`, `restream_url`, and `restream_provider`. For cameras where no path works, it points to checking camera access or trying another stream source. When restreaming is recommended, `action_plan.provider_help` includes manual go2rtc and Frigate URL helper metadata that can be used today, plus planned WebRTC and transcoding provider notes for future support.

When restreaming is recommended, the response also includes `restream_source_suggestion` with candidate stream names, go2rtc/Frigate-style HLS/MJPEG URL patterns, provider help, and a safe follow-up `save_restream_source` payload.

Set `save_recommendation: true` to save the recommended stream strategy as per-camera defaults. Any explicit test fields, such as width, height, duration, position, snapshot fallback, stream camera entity, or snapshot camera entity, are saved with it. If no compatible stream is found, no defaults are saved.

After a compatibility test runs, the receiver device's `Last Camera Compatibility` sensor shows the latest recommended stream type. Its attributes include the tested camera, recommendation reason, action plan, stream availability results, source classification, and timestamp.

The receiver device also exposes a `Camera Restreaming Recommended` binary sensor. It turns on when the latest compatibility result says live video likely needs another TV-safe source, and its attributes include the camera entity, recommended stream type, recommendation reason, restreaming reason, next step, suggested options, current workaround paths, planned provider families, documentation URL, and timestamp.

The receiver device's `Saved Camera Defaults` sensor shows how many cameras have saved defaults. Its attributes list saved camera entities and restream-enabled cameras without exposing raw restream URLs, so you can confirm a camera is now using a saved TV-safe source from the device page.

After a real camera or snapshot action runs, the receiver device's `Last Camera Result` sensor shows whether the latest camera command was accepted or failed. Its attributes include the requested stream strategy, final stream type, source classification, transport, fallback usage, popup size, and failure reason where available. URLs are not stored.

The receiver device's `Last Command Result` sensor is the broader command audit trail. It records the latest receiver command type, accepted/failed status, transport, final stream type where applicable, failure stage, failure reason, and update time. Use it first when a popup, snapshot, or notification action behaves unexpectedly.

```yaml
service: ha_tv_pip.set_camera_defaults
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  stream_type: mjpeg_first
  stream_camera_entity: camera.front_door_sub
  restream_provider: go2rtc
  restream_url: http://homeassistant.local:1984/api/stream.m3u8?src=front_door
  snapshot_fallback: true
  duration_seconds: 30
  position: top_right
  width: 720
  height: 405
```

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
  text_overlay: false
  position: top_right
```

The service defaults to the receiver's preferred stream strategy, or `stream_type: auto` when no receiver default is configured. Automatic mode checks the receiver's reported capabilities. If the receiver supports playable fallback, automatic mode resolves HLS first and also sends an optional MJPEG fallback URL when Home Assistant can create one, so the Android overlay can switch streams if the receiver later rejects HLS playback. If the receiver does not support playable fallback, automatic mode prefers MJPEG first when available to reduce decoder risk, then falls back through HLS and snapshot resolution. Advanced users can force `stream_type: hls`, force `stream_type: mjpeg`, prefer MJPEG with fallback using `stream_type: mjpeg_first`, or force `stream_type: snapshot`.
`stream_type: mjpeg` uses Home Assistant's camera proxy stream endpoint and the receiver's overlay renderer. It is useful when a camera exposes an MJPEG stream that is more reliable on Android TV than its HLS profile. Use `stream_type: mjpeg_first` when MJPEG usually works best but HLS should still be tried before falling back to a snapshot.
`stream_camera_entity` is optional and defaults to `camera_entity`; set it when a lower-resolution, H.264, or MJPEG camera entity is more reliable for live playback on Android TV. `restream_url` is optional and takes precedence over Home Assistant camera stream resolution for live video; use it for a known TV-safe HLS or MJPEG URL from go2rtc or another local restreaming tool. When `snapshot_fallback` is enabled, the integration also sends a snapshot preview so the receiver can show a still image while the video stream loads. `snapshot_camera_entity` is optional and defaults to `camera_entity`; set it when a separate camera entity provides a better still image or substream preview.
`title`, `message`, and the styling fields are optional; when either `title` or `message` is present, the receiver renders the text below the camera or snapshot inside the same rounded glass popup by default. Set `text_overlay: true` to place the title/message over the media instead. Width and height can be used by themselves to resize the media popup without showing a text footer.
If a receiver reports that a requested stream type, snapshot mode, notification mode, or media text footer is unsupported, Home Assistant stops before sending the command and returns a clear service error. Older receivers that do not report capabilities keep the previous best-effort behaviour.
For cameras with multiple streams, use a TV-compatible H.264/HLS stream where possible, or try `stream_type: mjpeg` when HLS is unsupported on the receiver. Lower-resolution secondary streams are often more reliable for TV popups than high-resolution main streams. The receiver enables Media3 decoder fallback, but unsupported camera codecs still need a compatible camera profile, MJPEG fallback, go2rtc/WebRTC, or future transcoding support.

Automatic restreaming providers are not active yet. Manual `restream_url` support is available for users who already expose a TV-safe HLS or MJPEG source. Compatibility and calibration responses include manual provider helper metadata for go2rtc and Frigate-style restream URLs, including example URL patterns and the `set_camera_defaults` fields to save once a URL works. Diagnostics include a planned provider section so future support tooling can distinguish "manual URL configured" from "automatic provider not implemented". HLS, MJPEG, and snapshots remain the supported receiver paths today.

The receiver device also exposes a `Restreaming Provider Status` sensor. It reports `planned` today, with attributes for configured, active, supported, and planned providers. This is intentionally a visibility surface only; it does not enable go2rtc, WebRTC, or transcoding yet.

## Restream Source Helper 🧵

Use `ha_tv_pip.save_restream_source` after testing a go2rtc or similar restream URL from the TV network:

```yaml
service: ha_tv_pip.save_restream_source
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  restream_url: http://homeassistant.local:1984/api/stream.m3u8?src=front_door
  restream_provider: go2rtc
  snapshot_fallback: true
  width: 720
  height: 405
```

The helper saves the URL as the camera's live source, defaults the provider label to `go2rtc`, keeps snapshot fallback enabled unless disabled, and infers `hls` or `mjpeg` from common URL shapes when `stream_type` is omitted. Its response includes `defaults_summary`, which confirms the saved provider, stream type, and `has_restream_url` without echoing the URL. After saving, normal automations can call `ha_tv_pip.show_camera` with only `camera_entity`. Check the receiver device's Saved Camera Defaults sensor to confirm the camera has a saved restream source without exposing the URL.

To get candidate stream names and URL patterns before saving a manual source:

```yaml
service: ha_tv_pip.suggest_restream_source
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  restream_provider: frigate
  restream_base_url: http://frigate.local:1984
```

To validate one candidate before saving it:

```yaml
service: ha_tv_pip.test_restream_source
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  restream_url: http://homeassistant.local:1984/api/stream.m3u8?src=front_door
  restream_provider: go2rtc
  check_reachability: false
  save: false
```

The action returns `stream_type`, `url_shape`, `receiver_supports_stream_type`, `reachability`, `save_recommended`, `next_step`, and a `save_action` payload when the URL should be saved. Provider base URLs such as `http://go2rtc.local:1984` are accepted for validation but are not recommended for saving; use a playable endpoint such as `/api/stream.m3u8?src=<stream_name>` or `/api/stream.mjpeg?src=<stream_name>`. Keep `check_reachability: false` if the candidate URL is only reachable from the TV network or you only want to check URL shape and receiver capability support. Set `save: true` to save the restream source automatically when validation passes.

This is advisory only. It does not create go2rtc streams or validate the returned URLs automatically.

To reset all saved camera compatibility choices for a receiver:

```yaml
service: ha_tv_pip.clear_all_camera_defaults
target:
  device_id: living_room_tv
```

The response includes `cleared_camera_count` and `cleared_cameras` so you can confirm which saved camera defaults were removed.

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

The service sends a styled text notification to the paired receiver as `streamType: notification`. It is useful for alert-style messages that do not need a camera stream or snapshot. Position values are `top_right`, `top_left`, `bottom_right`, and `bottom_left`; colors must be six-digit or alpha hex values. Optional `width` and `height` values are pixels; when omitted, the receiver defaults are used first, then text-only notifications default to `512px` wide and content height while media popups default to `640x360`. Notifications use rounded glass-style containers on the TV.

## Remote Receiver Mode 🌍

Phase 9 adds optional remote receiver transport for external TVs.

The integration registers a Home Assistant WebSocket command that a paired Android TV receiver can use after authenticating to the user's own Home Assistant instance. `ha_tv_pip.show_camera`, `ha_tv_pip.show_snapshot`, `ha_tv_pip.show_notification`, Test PiP, Close PiP, Refresh Status, and receiver status polling use local HTTP first by default. Prefer Remote Transport can be enabled per receiver for WebSocket-first behavior, and the non-preferred path remains available as fallback when possible.

Remote mode is not a HA TV PiP cloud service. It uses the user's Home Assistant external URL, including Nabu Casa URLs where available, and the integration remains `local_push`.

## Known Limitations 🚧

- Some Android TV devices reject native PiP for sideloaded apps; the receiver includes an overlay fallback when permission is granted.
- High-resolution or non-H.264 camera streams may not decode on every TV device.
- Transcoding, WebRTC support, Play Store production deployment, default HACS inclusion, and official Home Assistant core submission are future goals.
- Tier 1 translations are implemented for current surfaces, but native-speaker review is still pending.

## Translations 🌍

English is the source language for the integration.

Home Assistant UI strings live in `strings.json` and `translations/*.json`. Tier 1 translation files are in place for the Phase 10 polish pass and tracked in `../../../docs/translations.md`.
