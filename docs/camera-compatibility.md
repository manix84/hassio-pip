# Camera Compatibility 📹🧵

HA TV PiP can show Home Assistant camera popups when the receiver gets a stream or snapshot path that the TV can actually display.

This page explains what "TV-safe" means today, how to use the current compatibility tools, and how future restreaming providers such as go2rtc, WebRTC, or transcoding should fit into the project.

## Current Support ✅

The Home Assistant integration can currently resolve and send:

- HLS camera streams through Home Assistant's stream API.
- MJPEG streams through Home Assistant's camera proxy stream endpoint.
- Snapshot images through Home Assistant's camera proxy image endpoint.
- Optional snapshot previews while a live stream loads.
- Optional MJPEG fallback URLs when the receiver can switch away from a failed HLS playback attempt.

The Android TV receiver can currently display:

- HLS streams supported by Android Media3 / ExoPlayer on the receiver device.
- MJPEG streams through the overlay renderer.
- Snapshot images.
- Camera and snapshot popups with optional title/message footers.

## TV-Safe Stream Source 🛟

A TV-safe source is a stream or image source that Home Assistant can resolve and the receiver can display reliably.

In practice, that usually means:

- The URL is reachable by the Android TV receiver.
- The Home Assistant token or paired receiver token is valid.
- The camera entity exposes HLS, MJPEG, or snapshot output through Home Assistant.
- The video codec/profile is supported by the Android TV device.
- The stream is not too high-resolution or too demanding for the receiver hardware.
- A lower-resolution substream or MJPEG stream is available when the main stream is not TV-friendly.

Unsupported high-resolution camera main streams are expected to fail on some Android TV devices. HA TV PiP can fall back to snapshots or MJPEG where possible, but it cannot turn an unsupported codec into a supported one without a future restreaming or transcoding provider.

## Recommended Workflow 🧭

Use `ha_tv_pip.setup_camera` first:

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
  save: false
```

Review the returned `setup_mode`, `setup_summary`, `setup_steps`, `summary`, `action_plan`, `recommended_stream_type`, `recommended_defaults`, `restreaming_recommended`, `restreaming_next_step`, `restreaming_options`, and `restreaming_provider`.

`setup_camera` runs the normal calibration workflow when no `restream_url` is supplied. If you provide a candidate `restream_url`, it switches to restream validation and can save the source in the same action with `save: true`.

The `setup_steps` list is an ordered checklist for UI helpers and troubleshooting. Each step includes a stable key, label, status, and any relevant follow-up action or validation details.

The `action_plan` block is the fastest path for normal users. It includes:

- `primary_action`: stable key for dashboards or support tools.
- `primary_action_label`: human-readable next step.
- `service`: the next HA TV PiP service to call.
- `data`: a safe payload for that service. Direct restream URLs are not duplicated here; review `recommended_defaults` when a restream URL is involved.
- `fields_to_try`: optional fields to adjust when live video needs another source.
- `provider_help`: helper metadata for manual go2rtc URLs today, plus planned WebRTC/transcoding paths for future support.
- `notes`: short guidance explaining why that action was recommended.

When the recommendation looks right, run the same action with `save: true`. The saved per-camera defaults can include stream type, stream camera entity, snapshot camera entity, snapshot fallback, duration, position, width, and height.

If you already expose a TV-safe restream through go2rtc or another tool, save it as the camera's live source:

```yaml
service: ha_tv_pip.save_restream_source
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  restream_url: http://homeassistant.local:1984/api/stream.m3u8?src=front_door
  restream_provider: go2rtc
  snapshot_fallback: true
```

The helper defaults the provider to `go2rtc`, keeps snapshot fallback enabled, and infers `hls` or `mjpeg` from common URL shapes when `stream_type` is omitted. The receiver still uses `camera_entity` for titles and snapshot previews, but live video comes from the saved restream URL. Saved restream URLs are redacted from diagnostics and are not exposed by the Saved Camera Defaults sensor.

If you need help building the manual restream values, run:

```yaml
service: ha_tv_pip.suggest_restream_source
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  restream_base_url: http://homeassistant.local:1984
```

The response includes candidate stream names, go2rtc/Frigate-style HLS/MJPEG URL patterns, provider help, and a `save_action` payload to use after you have tested a working URL. `restream_base_url` is optional; omit it to use the provider default suggestion. This is advisory only; it does not create provider streams automatically.

Before saving one candidate, validate it with:

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

This action infers HLS or MJPEG from the URL, checks that the URL looks like a playable stream endpoint, checks the selected receiver's capability metadata, optionally checks reachability from Home Assistant, and returns a `save_action` payload when the candidate looks worth saving. Provider base URLs such as `http://go2rtc.local:1984` are accepted for validation but return `save_recommended: false`; use a playable endpoint such as `/api/stream.m3u8?src=<stream_name>` or `/api/stream.mjpeg?src=<stream_name>`. Keep `check_reachability: false` for candidate URLs that may only be reachable from the TV network. Set `save: true` to save the candidate as per-camera defaults in the same action when validation passes.

When calibration or compatibility testing recommends restreaming, the action response includes the same guidance in `restream_source_suggestion` so you can move directly from a failed or snapshot-only live path to candidate manual restream values.

Future automations can then stay small:

```yaml
service: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
```

If you want to reset all saved camera compatibility choices for a receiver, use:

```yaml
service: ha_tv_pip.clear_all_camera_defaults
target:
  device_id: living_room_tv
```

The response includes `cleared_camera_count` and `cleared_cameras`, and the receiver device's `Saved Camera Defaults` sensor should return to `0`.

## Manual Restream Helper Workflow 🧰

Automatic restream provider setup is not implemented yet, but the calibration response exposes enough helper metadata to guide manual setup for TV-safe HLS/MJPEG sources such as go2rtc or Frigate's bundled go2rtc endpoint:

- `restreaming_provider.manual_provider_workflows`: current provider workflows that can be used today.
- `action_plan.provider_help.manual_provider_workflows`: the same helper data attached to the suggested next action.
- `example_url_patterns`: example HLS and MJPEG URL shapes for a provider stream name.
- `service` and `fields`: the HA TV PiP service and fields to use when saving the working URL as per-camera defaults.

The current manual restream path is:

1. Create or identify a TV-safe stream name for the camera.
2. Run `ha_tv_pip.suggest_restream_source` to get candidate stream names and URL patterns.
3. Test the HLS or MJPEG URL from a device on the same network as the TV.
4. Run `ha_tv_pip.test_restream_source` to confirm URL shape and receiver stream support. Use `save: true` when you want the action to save the source automatically after validation passes.
5. Save that URL with `ha_tv_pip.save_restream_source`.
6. Keep `snapshot_fallback: true` so the receiver can show an image while live video loads or if live video fails.
7. Check the receiver device's `Saved Camera Defaults` sensor to confirm the camera has a saved restream source.

Example URL patterns:

```txt
http://homeassistant.local:1984/api/stream.m3u8?src=<stream_name>
http://homeassistant.local:1984/api/stream.mjpeg?src=<stream_name>
http://frigate.local:1984/api/stream.m3u8?src=<camera_name>
http://frigate.local:1984/api/stream.mjpeg?src=<camera_name>
```

Treat these as provider helper patterns, not guaranteed URLs. Your actual host, port, stream name, Frigate camera name, and go2rtc configuration may differ.

## When Restreaming Is Recommended 🧵

The integration can flag a camera as needing a TV-safe restreamed source when:

- HLS and MJPEG are unavailable for the selected camera path.
- Only snapshots are available, which is useful for alerts but not live video.
- The selected camera entity resolves a stream that is likely unsupported by the receiver.

When this happens, try these before changing automations everywhere:

- Use `stream_camera_entity` with a lower-resolution camera entity.
- Use `snapshot_camera_entity` with a faster still-image entity.
- Try `stream_type: mjpeg` or `stream_type: mjpeg_first` if the camera exposes MJPEG.
- Use the camera's H.264 substream or compatibility profile when available.
- Use `restream_url` with a known TV-safe HLS or MJPEG URL from go2rtc or another local restreaming tool.
- Save working settings as per-camera defaults.
- Use `ha_tv_pip.clear_all_camera_defaults` if you want to wipe saved compatibility choices for a receiver and recalibrate from scratch.

## Future Provider Model 🚧

Automatic restreaming providers are not implemented yet. Manual `restream_url` support is available for users who already expose a TV-safe HLS or MJPEG URL. Diagnostics still expose a planned inactive provider block so support tools and future UI can report that automatic provider support is intentionally unavailable rather than silently missing.

The provider status metadata also includes today's recommended paths:

- `use_stream_camera_entity`: point the automation at a known TV-safe stream entity.
- `use_mjpeg_first`: prefer MJPEG first when a camera exposes both HLS and MJPEG.
- `use_snapshot_fallback`: show a still image while live video loads or when live video fails.
- `use_camera_substream`: choose a lower-resolution or H.264 compatibility profile.
- `use_restream_url`: point the camera default at a known TV-safe HLS or MJPEG restream URL.
- `save_per_camera_defaults`: store the working values once a camera has been calibrated.

Provider roadmap:

- `go2rtc`: manual `restream_url` support and helper metadata work today; guided setup helpers remain future work.
- `WebRTC`: future low-latency path where the receiver and platform constraints allow it.
- `transcoding`: future optional path for converting unsupported camera formats into receiver-compatible video.

These future providers should be optional. The local-first HLS, MJPEG, and snapshot path should remain the default for users whose cameras already expose TV-safe streams.

## Troubleshooting Notes 🩺

- Check the receiver device's `Last Camera Compatibility` sensor after running a compatibility test.
- Check the receiver device's `Saved Camera Defaults` sensor after saving a recommendation or restream source. Its attributes list saved cameras and restream-enabled cameras without exposing raw restream URLs.
- Check the `Camera Restreaming Recommended` binary sensor when live video falls back to snapshots. Its attributes include current workaround paths, planned provider families, and a documentation URL.
- Check the `Last Command Result` sensor after any popup command for command type, accepted/failed status, transport, final stream type, failure stage, and failure reason.
- Check the `Last Camera Result` sensor after a real camera or snapshot command. `stream_source` shows whether the command used the main camera entity, alternate stream entity, snapshot entity, or manual restream URL.
- Download diagnostics from the Home Assistant integration entry when opening an issue. URLs and tokens are redacted.
- If remote receiver mode is used, confirm the TV can reach the configured Home Assistant external URL.
