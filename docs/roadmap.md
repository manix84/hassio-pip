# Roadmap

## Project Goal

**HA TV PiP** is a paired Home Assistant + Android TV project.

The goal is to let Home Assistant automations display security camera feeds, snapshots, alerts, or other visual notifications on Android TV / Google TV devices using Picture-in-Picture or lightweight overlay-style playback.

The project is split into three main parts:

```txt
android-tv-app/
  Android TV receiver app.

ha-integration/
  Home Assistant custom integration.

website/
  Promotional website and documentation entry point.
```

The Android TV app should act as the receiver.

The Home Assistant integration should act as the controller.

The website should explain the project, current status, roadmap, and release paths.

The intended user experience is:

```txt
1. User installs the Android TV app.
2. User installs the Home Assistant integration.
3. Home Assistant discovers the TV app automatically on the LAN.
4. User pairs the discovered device.
5. Automations can call a Home Assistant service to show a camera feed on the TV.
```

---

# Phase 1: Android TV PiP MVP ✅

Status: Complete in `0.4.0`.

## Goal

Prove that an Android TV app can reliably play a video stream and display it outside the full-screen app using native Picture-in-Picture where available, or a local overlay fallback where Android TV does not expose native PiP.

## Scope

- Android TV Kotlin app.
- Public test HLS playback.
- Media3 ExoPlayer.
- Manual PiP entry.
- Automatic PiP entry when Home is pressed.
- No-ADB overlay fallback for Google TV devices that reject native PiP.
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
- User can manually enter native PiP where supported.
- User can manually show the overlay fallback where native PiP is unavailable.
- Pressing Home while video is playing enters native PiP or starts the overlay fallback where supported.
- Playback continues in PiP or overlay mode.
- App handles pause/resume/close cleanly.

---

# Phase 2: Local Control Endpoint ✅

Status: Complete in `0.6.0`.

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

Completed behaviour:

- The Android TV app starts an unauthenticated local HTTP endpoint on port `8765`.
- `GET /status` reports app version, stable device id, playback state, display mode, title, and URL.
- `POST /show` accepts HLS commands.
- `POST /close` closes playback and stops the overlay fallback.
- On Google TV devices that reject native PiP, `enterPip: true` can start the overlay fallback directly.
- Duplicate `/show` commands replace the current playback or overlay.
- `durationSeconds` is enforced for both full-screen playback and the overlay fallback.
- The Android TV main screen shows the local control endpoint address when available.
- `/status` includes endpoint uptime, request count, and previous request diagnostics.
- The Android TV main screen shows live endpoint state, uptime, request count, and previous request diagnostics.
- `/close` reports whether playback was active and which display mode was closed.
- `GET /` reports API metadata and supported endpoints.
- Known endpoints return `405 Method Not Allowed` when called with the wrong HTTP method.
- Unknown endpoints return `404 Not Found` with a JSON error response.

## Success Criteria

- A developer can trigger playback from another machine using `curl`.
- A developer can close playback using `curl`.
- The app remains stable if duplicate `/show` commands arrive.
- Invalid requests return clear errors.

---

# Phase 3: mDNS / Local Network Discovery ✅

Status: Complete in `0.14.1`.

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

Initial `0.7.0` Android behaviour:

- The Android TV app advertises `_ha-tv-pip._tcp.local.` with Android NSD while the local endpoint is running.
- Advertised metadata includes stable device id, receiver name, app version, pairing state, and API version.
- `GET /status` reports discovery state, service name, service type, port, and registration errors.
- The Android TV main screen reports whether discovery is advertising.

Initial `0.8.0` Home Assistant behaviour:

- The Home Assistant integration declares a Zeroconf matcher for `_ha-tv-pip._tcp.local.`.
- The Home Assistant config flow can create or update a receiver config entry from discovered metadata.

Completed behaviour:

- The Android TV app advertises `_ha-tv-pip._tcp.local.` while the local control endpoint is running.
- Advertised TXT metadata includes stable device id, receiver name, app version, pairing state, and API version.
- `GET /status` reports discovery state and current service registration details.
- Home Assistant discovers receivers automatically and shows a discovered device card.
- Discovery setup confirms the receiver name before creating a config entry.
- Existing config entries are updated when the same receiver is rediscovered with new host, port, version, pairing, or API metadata.
- Multiple receivers can be represented independently by stable receiver id.

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

# Phase 4: Device Pairing and Local Authentication ✅

Status: Complete in `0.18.0`.

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

Current behaviour:

- The receiver starts in `pairing=required`.
- `POST /pair/start` starts a five-minute pairing window and shows a six-digit code on the TV only.
- `POST /pair/confirm` exchanges the TV-visible code for a bearer token.
- Existing pairings cannot be replaced remotely; the user must choose `Reset Pairing` on the TV app first.
- `/show` and `/close` reject unauthenticated requests once pairing is required or complete.
- Discovery metadata refreshes when pairing starts, completes, or resets.

## Home Assistant Integration Requirements

- Add config flow steps for pairing.
- Store token in config entry data.
- Never expose the token in logs.
- Handle pairing failures clearly.
- Allow reauthentication if token becomes invalid.

Current behaviour:

- Discovery setup starts pairing when the receiver reports pairing is required.
- Home Assistant asks the user for the code shown on the TV.
- The returned token is stored in config entry data and is not logged.
- If the receiver is already paired, Home Assistant asks the user to reset pairing from the TV app.

## Success Criteria

- Unpaired requests are rejected.
- Paired Home Assistant instance can control the TV.
- Pairing can be reset from the TV app.
- Integration can recover from failed or expired pairing.

---

# Phase 5: Home Assistant Service MVP

Status: Complete in `0.21.0`.

## Goal

Expose a Home Assistant service that can show a camera feed on a paired Android TV device.

## Service

Initial service:

```yaml
action: ha_tv_pip.show_camera
data:
  receiver_device_id: living_room_tv
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

Initial behaviour:

- Registers `ha_tv_pip.show_camera`.
- Accepts `receiver_device_id`, `camera_entity`, `duration_seconds`, `enter_pip`, and optional `title`.
- Resolves HLS streams with Home Assistant's camera stream API.
- Sends authenticated `/show` commands to the paired receiver.
- Requires paired receiver config entries with stored tokens.
- Preserves receiver playback errors in `/status` for codec and stream debugging.
- Verified with a compatible lower-resolution camera stream; high-resolution or non-H.264 streams can fail on receiver devices when the camera codec/profile is unsupported.
- Enables Media3 decoder fallback on the receiver before reporting unsupported codec/profile failures.

## Example Automation

```yaml
alias: Show front door on TV
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_bell_visitor
    to: "on"
action:
  - service: ha_tv_pip.show_camera
    data:
      receiver_device_id: living_room_tv
      camera_entity: camera.front_door_bell
      duration_seconds: 30
      enter_pip: true
```

## Success Criteria

- Home Assistant automation can trigger a TV PiP camera popup.
- Errors are visible and understandable in Home Assistant logs.
- Receiver playback errors are visible through the receiver status endpoint.
- Multiple configured TVs can be targeted separately with `receiver_device_id`.

## Completion Notes

- Completed and tested with Home Assistant triggering a paired Chromecast receiver.
- Compatible lower-resolution stream playback is confirmed working through `ha_tv_pip.show_camera`.
- High-resolution or non-H.264 stream playback can fail when the stream codec/profile is unsupported by Android TV hardware decoders.
- The receiver now enables Media3 decoder fallback and shows an actionable unsupported-stream message instead of a silent black box.
- Broad main-stream support remains a future capability requiring stream profile selection, restreaming, or transcoding.

---

# Phase 6: Snapshot Support

Status: Complete in `0.22.0`.

## Goal

Support still image popups for cameras or alerts where video is unnecessary or unreliable.

## Service

```yaml
action: ha_tv_pip.show_snapshot
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 10
  enter_pip: true
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

## Completion Notes

- Completed and tested with Home Assistant triggering a paired Chromecast receiver.
- `ha_tv_pip.show_snapshot` displays camera snapshots through the Android TV overlay renderer.
- Snapshot commands use the same pairing, bearer-token auth, receiver targeting, and duration timeout as video commands.
- Camera feeds and snapshot feeds were both tested successfully from Home Assistant before moving to Stage 7.

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

# Future Goal: Receiver Management Mode

## Goal

Allow the Android TV receiver to behave more like an appliance than a normal foreground app after setup.

## Ideas

- Optional setting to hide the receiver app from the Android TV / Google TV launcher after pairing.
- Clear instructions for how to find, reopen, or recover the app after it has been hidden.
- Home Assistant controls to reopen receiver settings, diagnostics, pairing reset, or overlay permission guidance.
- Receiver diagnostics exposed through Home Assistant so users do not need to open the TV app for routine troubleshooting.
- A safe recovery path if Home Assistant is unavailable or pairing is broken.
- Service-first receiver behavior so PiP / overlay requests keep working without the user manually opening the app.

## Notes

This needs careful UX design. If the app can be hidden from the launcher, users still need a reliable way to access settings, reset pairing, view debug information, and recover from bad configuration.

The hide option should include explicit instructions before and after it is enabled. Users should know where the receiver can still be found, how Home Assistant can reopen it, and what fallback path exists if Home Assistant cannot reach it.

The receiver service must continue to start and accept authenticated local commands after reboot without requiring a user to open the app first. Hiding the launcher icon must not make PiP or overlay requests depend on foreground app launch.

Implementation may require Android manifest alias components or launcher category toggling. This should be tested carefully on Android TV, Google TV, Fire TV / Vega OS, and any future receiver platforms because launcher behavior varies by vendor.

## Success Criteria

- Users can optionally hide the app from the TV launcher.
- Home Assistant can request the receiver settings or diagnostics screen to open.
- Users can recover access without ADB.
- Debug and pairing reset workflows remain available after hiding the launcher icon.
- PiP and overlay commands still work after reboot without manually opening the app.

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
- Work toward official Home Assistant integration readiness.
- Add documentation.
- Add example automations.
- Add diagnostics.
- Add issue templates.
- Add release notes.

## Success Criteria

- User can install the app from the Android TV Play Store.
- User can install the integration through HACS.
- Setup is understandable without reading source code.

## Official Home Assistant Track

HACS is the practical first distribution target for the custom integration.

Longer term, HA TV PiP should work toward official Home Assistant integration readiness. That means keeping the integration local-first, well tested, documented, secure by default, and aligned with Home Assistant architecture and quality expectations.

Official inclusion should not block the MVP, Stage 5 service work, or HACS distribution, but design decisions should avoid making an upstream contribution harder later.

---

# Website Track: Promotional Site

## Goal

Provide a static project landing page suitable for GitHub Pages.

## Scope

- Vite.
- React.
- TypeScript.
- SCSS Modules.
- Current project status.
- Roadmap preview.
- Example automation.
- Release and documentation links.

## Out of Scope

- Full documentation platform.
- Backend services.
- Analytics.
- Authentication.
- Release generation.

## Success Criteria

- Website builds successfully.
- Website reflects current MVP status honestly.
- Website can be deployed to GitHub Pages.

---

# Long-Term Ideas

These should not block the MVP.

- Fire TV / Vega OS receiver app.
- Exploratory Apple TV / tvOS receiver app.
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
- Broad video format support through stream capability detection, restreaming, or transcoding so high-quality camera main streams can work on receiver devices.
- Companion mobile app support.
- Local-only privacy mode.
- Import/export settings.

## Additional TV Platforms

HA TV PiP should avoid assuming Android TV and Google TV are the only possible receiver platforms.

Fire TV and Vega OS are the most natural next platform family because they are closer to the Android receiver model and may be able to share protocol concepts, pairing flow, and Home Assistant integration behavior.

Apple TV support is desirable but exploratory. tvOS has different constraints around background execution, Picture-in-Picture behavior, app distribution, and local-network control, so it may require a separate receiver design rather than a direct port.

Future platform work should keep the local receiver protocol platform-neutral so Home Assistant can target receiver capabilities rather than Android-specific behavior.
