# Troubleshooting 🩺

Use this guide when setup, pairing, receiver control, camera playback, or remote receiver mode does not behave as expected.

HA TV PiP is still in beta. The most useful support data is the Android receiver version, Home Assistant integration version, Home Assistant version, TV model, camera platform, selected stream strategy, and redacted Home Assistant diagnostics.

## Quick Checks ✅

1. Confirm the Android TV receiver app and Home Assistant integration are on the same release version.
2. Confirm the receiver app has been opened at least once after install or update.
3. Confirm Home Assistant and the TV are on the same network for local discovery and local control.
4. Open the receiver app dashboard and check that the local endpoint is running.
5. In Home Assistant, open the receiver device and check receiver status, compatibility, and last camera result sensors.
6. Download config entry diagnostics before opening a bug report. Tokens and active stream URLs are redacted by the integration.

## Discovery Card Does Not Appear 🔎

- Confirm the TV and Home Assistant host are on the same LAN or VLAN.
- Confirm multicast / mDNS / Zeroconf traffic is allowed between Home Assistant and the TV.
- Keep the Android receiver app open during setup so the service advertisement is active.
- Check the receiver dashboard for discovery status.
- Use manual setup only as a fallback when discovery is blocked but the TV IP address is reachable.

## Pairing Problems 🔐

- Pairing is intentionally TV-visible. Home Assistant starts pairing, and the six-digit code appears on the TV.
- If the receiver is already paired with another Home Assistant instance, use `Reset Pairing` in the TV app before pairing again.
- If the pairing code expires, restart pairing from Home Assistant.
- Existing pairings cannot be replaced remotely. This prevents another LAN client from taking over a receiver.

## Popup Does Not Appear 📺

- Check the receiver device's connected sensor in Home Assistant.
- Use the receiver device's Test PiP button to verify basic receiver control.
- If native Android TV PiP is unavailable, HA TV PiP should use the local overlay fallback when overlay permission is granted.
- Confirm the receiver has not been paused by TV power management or network sleep settings.
- If remote receiver mode is used, confirm the TV can reach the configured Home Assistant external URL.

## Video Is Black, Unsupported, Or Falls Back To Snapshot 📹

Android TV devices can reject unsupported codecs, high resolutions, or camera profiles. This is a stream compatibility issue rather than a pairing issue.

Try this order:

1. Run `ha_tv_pip.calibrate_camera` with `save: false`.
2. Inspect `recommended_defaults`, `recommended_stream_type`, `restreaming_recommended`, `restreaming_next_step`, and `restreaming_options`.
3. Try a lower-resolution or H.264 substream with `stream_camera_entity`.
4. Try `stream_type: mjpeg_first` or `stream_type: mjpeg` when the camera exposes MJPEG.
5. Keep `snapshot_fallback: true` for useful alerts while live compatibility is being tuned.
6. If you already have go2rtc or another TV-safe HLS/MJPEG stream, save it with `restream_url` and `restream_provider`.
7. Save working values with `ha_tv_pip.set_camera_defaults` or `ha_tv_pip.calibrate_camera` using `save: true`.

See [Camera Compatibility](camera-compatibility.md) for the full workflow.

## Launcher Is Hidden 🕹️

If the receiver app is hidden from the Android TV launcher:

- Use the Home Assistant receiver device's Open Launcher button.
- Or open Android Settings > Apps > HA TV PiP.
- PiP, snapshot, and notification commands should not require the user to manually open the app first after normal receiver startup behavior is available on the TV.

## Remote Receiver Not Connected 🌍

- Confirm the Home Assistant external URL is reachable from the TV network.
- Confirm the remote receiver token is current.
- Use the Home Assistant Sync Remote Config control after changing remote settings.
- Local LAN control remains preferred when the TV is at home.
- Remote receiver mode is not a HA TV PiP cloud service; it uses the user's own Home Assistant WebSocket API.

## What To Include In A Bug Report 🐛

Include:

- Android receiver version.
- Home Assistant integration version.
- Home Assistant version.
- TV / streaming device model and Android TV version.
- Camera platform or model when the issue involves video.
- Stream strategy used: `auto`, `hls`, `mjpeg`, `mjpeg_first`, `snapshot`, or `restream_url`.
- The service call or automation YAML with private details redacted.
- Config entry diagnostics from Home Assistant.
- Receiver `/status` output only after removing private URLs, bearer tokens, pairing codes, device IDs, and camera details.
