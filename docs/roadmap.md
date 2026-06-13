# Roadmap

## Project Goal

**HA TV PiP** is a paired Home Assistant + Android TV project.

The goal is to let Home Assistant automations display security camera feeds, snapshots, alerts, or other visual notifications on Android TV / Google TV devices using Picture-in-Picture or lightweight overlay-style playback.

The project is split into two main parts:

```txt
android-tv-app/
  Android TV receiver app.

ha-integration/
  Home Assistant custom integration.
```

The Android TV app should act as the receiver.

The Home Assistant integration should act as the controller.

The intended user experience is:

```txt
1. User installs the Android TV app.
2. User installs the Home Assistant integration.
3. Home Assistant discovers the TV app automatically on the LAN.
4. User pairs the discovered device.
5. Automations can call a Home Assistant service to show a camera feed on the TV.
```

---

# Phase 1: Android TV PiP MVP

## Goal

Prove that an Android TV app can reliably play a video stream and enter Picture-in-Picture mode.

## Scope

- Android TV Kotlin app.
- Public test HLS playback.
- Media3 ExoPlayer.
- Manual PiP entry.
- Automatic PiP entry when Home is pressed.
- Basic TV-friendly UI.
- Basic logging and error handling.

## Out of Scope

Do not implement yet:

- Home Assistant integration.
- Local HTTP control.
- mDNS discovery.
- Pairing.
- Authentication.
- Camera entity support.
- Remote access.

## Success Criteria

- App launches on Android TV / Google TV.
- User can play a public test HLS stream.
- User can manually enter PiP.
- Pressing Home while video is playing enters PiP where supported.
- Playback continues in PiP.
- App handles pause/resume/close cleanly.

---

# Phase 2: Local Control Endpoint

## Goal

Allow another device on the LAN to command the Android TV app to show or close a video.

## Android TV App Requirements

Add a small local control server inside the Android TV app.

Initial endpoints:

```txt
GET  /status
POST /show
POST /close
```

Example `/status` response:

```json
{
  "app": "HA TV PiP Receiver",
  "version": "0.1.0",
  "deviceId": "stable-device-id",
  "deviceName": "Living Room TV",
  "pairingRequired": false,
  "playbackState": "idle"
}
```

Example `/show` request:

```json
{
  "title": "Front Door",
  "url": "https://example.com/test-stream.m3u8",
  "streamType": "hls",
  "durationSeconds": 30,
  "enterPip": true
}
```

## Behaviour

- `/show` launches the player activity.
- The player starts playback.
- The player enters PiP if requested.
- The player auto-closes after `durationSeconds` if provided.
- `/close` stops playback and closes the player.

## Success Criteria

- A developer can trigger playback from another machine using `curl`.
- A developer can close playback using `curl`.
- The app remains stable if duplicate `/show` commands arrive.
- Invalid requests return clear errors.

---

# Phase 3: mDNS / Local Network Discovery

## Goal

Allow Home Assistant to discover the Android TV app automatically on the local network.

## Android TV App Requirements

Advertise a local network service using Android Network Service Discovery.

Suggested service type:

```txt
_ha-tv-pip._tcp.local.
```

Advertised metadata should include:

```txt
id=stable-device-id
name=Living Room TV
version=0.1.0
pairing=required|paired|disabled
api=1
```

## Home Assistant Integration Requirements

Add Zeroconf discovery support for:

```txt
_ha-tv-pip._tcp.local.
```

When a device is discovered:

- Create a discovery config flow.
- Show the discovered device name.
- Store host, port, device id, and version.
- If an existing device is rediscovered with a new IP, update the stored connection details.

## Success Criteria

- Installing the TV app causes Home Assistant to show a discovered device.
- Rebooting the TV or changing IP does not require manual reconfiguration.
- Multiple TVs can be discovered independently.

---

# Phase 4: Device Pairing and Local Authentication

## Goal

Secure local control so that random LAN devices cannot trigger camera popups.

## Pairing Flow

Suggested flow:

```txt
1. Home Assistant discovers the TV app.
2. User starts setup from Home Assistant.
3. TV app displays a short pairing code.
4. User enters the pairing code in Home Assistant.
5. Home Assistant and TV app exchange/store a shared token.
6. Future requests use the token.
```

## Android TV App Requirements

Add endpoints:

```txt
POST /pair/start
POST /pair/confirm
```

After pairing:

- Store the paired Home Assistant instance id.
- Store a local auth token securely.
- Reject unauthenticated `/show` and `/close` requests.
- Provide a UI option to reset pairing.

## Home Assistant Integration Requirements

- Add config flow steps for pairing.
- Store token in config entry data.
- Never expose the token in logs.
- Handle pairing failures clearly.
- Allow reauthentication if token becomes invalid.

## Success Criteria

- Unpaired requests are rejected.
- Paired Home Assistant instance can control the TV.
- Pairing can be reset from the TV app.
- Integration can recover from failed or expired pairing.

---

# Phase 5: Home Assistant Service MVP

## Goal

Expose a Home Assistant service that can show a camera feed on a paired Android TV device.

## Service

Initial service:

```yaml
ha_tv_pip.show_camera:
  target:
    device_id: living_room_tv
  data:
    camera_entity: camera.front_door
    duration_seconds: 30
    enter_pip: true
```

## Integration Behaviour

The integration should:

- Validate the target TV receiver.
- Validate the camera entity.
- Resolve a usable stream URL.
- Send a `/show` command to the TV app.
- Log clear errors if the camera cannot be streamed.

## Example Automation

```yaml
alias: Show front door on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    target:
      device_id: living_room_tv
    data:
      camera_entity: camera.front_door_bell
      duration_seconds: 30
      enter_pip: true
```

## Success Criteria

- Home Assistant automation can trigger a TV PiP camera popup.
- Errors are visible and understandable in Home Assistant logs.
- Multiple configured TVs can be targeted separately.

---

# Phase 6: Snapshot Support

## Goal

Support still image popups for cameras or alerts where video is unnecessary or unreliable.

## Service

```yaml
ha_tv_pip.show_snapshot:
  target:
    device_id: living_room_tv
  data:
    camera_entity: camera.front_door
    duration_seconds: 10
    title: Front Door
```

## Behaviour

- Home Assistant captures or resolves a camera snapshot.
- Android TV app displays the image in a TV-friendly view.
- Optional PiP/overlay style can be used if practical.
- Snapshot closes after timeout.

## Success Criteria

- Snapshot popups work even when live streaming is unavailable.
- Snapshot mode is faster than video mode.
- Snapshot mode is suitable for doorbell/person alerts.

---

# Phase 7: Stream Type Options

## Goal

Support multiple stream types with sensible fallbacks.

## Supported Stream Types

Start simple, then expand:

```txt
snapshot
hls
mjpeg
webrtc
```

## Behaviour

Default mode should be automatic:

```txt
1. Prefer the most reliable Home Assistant-supported stream.
2. Fall back to snapshot if streaming fails.
3. Log which stream type was selected.
```

Advanced users should be able to force a stream type per service call.

Example:

```yaml
stream_type: hls
```

## Success Criteria

- Users can choose between speed, quality, and reliability.
- Failed streams do not leave the TV app stuck.
- Snapshot fallback works cleanly.

---

# Phase 8: Receiver Entities and Diagnostics

## Goal

Make each Android TV receiver visible and manageable from Home Assistant.

## Entities

Possible entities:

```txt
sensor.living_room_tv_pip_status
binary_sensor.living_room_tv_pip_connected
button.living_room_tv_pip_test
button.living_room_tv_pip_close
```

## Diagnostics

Include:

- App version.
- API version.
- Device id.
- Last seen.
- Last command.
- Last error.
- Current playback state.
- Local connection status.

## Success Criteria

- User can see whether each receiver is online.
- User can test a receiver from Home Assistant.
- Debug information is available without digging through logs.

---

# Phase 9: Remote Access

## Goal

Allow a travel Android TV / Google TV device to receive PiP commands from Home Assistant without requiring port forwarding.

## Preferred Direction

Remote devices should connect outbound to Home Assistant.

Avoid requiring Home Assistant to directly connect inbound to the remote TV.

Possible approaches:

```txt
1. TV app connects to Home Assistant external URL.
2. TV app maintains a WebSocket connection.
3. Home Assistant sends commands over that connection.
```

## Requirements

- Support Nabu Casa / Home Assistant Cloud URL.
- Support manually configured external Home Assistant URL.
- Support local-only mode for users who do not want remote access.
- Clearly indicate whether the current connection is local or remote.

## Success Criteria

- A remote Android TV device can connect back to Home Assistant.
- No router port forwarding is required.
- Local mode remains available and preferred when on the same LAN.

---

# Phase 10: App Store / Distribution Polish

## Goal

Make the app and integration easy for normal Home Assistant users to install.

## Android TV App

- Prepare Play Store release.
- Add app icon and banner.
- Add onboarding screen.
- Add pairing screen.
- Add troubleshooting screen.
- Add privacy-friendly messaging.
- Add crash-safe logging.

## Home Assistant Integration

- Prepare for HACS distribution.
- Add documentation.
- Add example automations.
- Add diagnostics.
- Add issue templates.
- Add release notes.

## Success Criteria

- User can install the app from the Android TV Play Store.
- User can install the integration through HACS.
- Setup is understandable without reading source code.

---

# Long-Term Ideas

These should not block the MVP.

- Multiple camera layouts.
- Cycling camera feeds.
- Doorbell-specific mode.
- Person-detected mode.
- Motion event thumbnails.
- Two-way audio.
- Android notification integration.
- Full-screen takeover mode.
- Per-room routing.
- Per-camera default settings.
- Quiet hours.
- Do-not-disturb integration.
- Overlay position and size options.
- Frigate integration helpers.
- go2rtc integration helpers.
- WebRTC low-latency mode.
- Companion mobile app support.
- Local-only privacy mode.
- Import/export settings.
