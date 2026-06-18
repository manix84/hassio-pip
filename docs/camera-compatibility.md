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

Use `ha_tv_pip.calibrate_camera` first:

```yaml
service: ha_tv_pip.calibrate_camera
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

Review the returned `summary`, `recommended_stream_type`, `recommended_defaults`, `restreaming_recommended`, `restreaming_next_step`, and `restreaming_options`.

When the recommendation looks right, run the same action with `save: true`. The saved per-camera defaults can include stream type, stream camera entity, snapshot camera entity, snapshot fallback, duration, position, width, and height.

Future automations can then stay small:

```yaml
service: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
```

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
- Save working settings as per-camera defaults.

## Future Provider Model 🚧

Restreaming providers are not implemented yet. Diagnostics expose a planned inactive provider block so support tools and future UI can report that provider support is intentionally unavailable rather than silently missing.

Planned provider families:

- `go2rtc`: future helper path for turning camera sources into TV-safe streams.
- `webrtc`: future low-latency path where the receiver and platform constraints allow it.
- `transcoding`: future path for converting unsupported camera formats into receiver-compatible video.

These future providers should be optional. The local-first HLS, MJPEG, and snapshot path should remain the default for users whose cameras already expose TV-safe streams.

## Troubleshooting Notes 🩺

- Check the receiver device's `Last Camera Compatibility` sensor after running a compatibility test.
- Check the `Camera Restreaming Recommended` binary sensor when live video falls back to snapshots.
- Check the `Last Camera Result` sensor after a real popup command.
- Download diagnostics from the Home Assistant integration entry when opening an issue. URLs and tokens are redacted.
- If remote receiver mode is used, confirm the TV can reach the configured Home Assistant external URL.
