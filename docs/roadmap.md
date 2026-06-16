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

# Phase 6: Snapshot Support ✅

Status: Complete in `0.23.0`.

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
- Video commands now support an optional entity-based snapshot preview fallback so a still image can be displayed while live playback loads.

---

# Phase 7: Stream Type Options ✅

Status: Complete in `0.24.0`.

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

Initial implementation:

- `stream_type: auto` prefers HLS and falls back to snapshot if Home Assistant cannot resolve an HLS stream.
- `stream_type: hls` forces HLS and reports stream resolution errors instead of changing modes.
- `stream_type: snapshot` sends a snapshot command through `ha_tv_pip.show_camera`.
- Receiver overlays keep the snapshot preview visible if video playback fails after the HLS URL is accepted.
- `mjpeg` and `webrtc` remain future stream types.

## Success Criteria

- Users can choose between speed, quality, and reliability.
- Failed streams do not leave the TV app stuck.
- Snapshot fallback works cleanly.

## Completion Notes

- Completed and tested with Home Assistant triggering a paired Chromecast receiver.
- `stream_type: auto`, `hls`, and `snapshot` are exposed through the Home Assistant service schema.
- Automatic mode falls back to a snapshot command when Home Assistant cannot resolve HLS.
- Receiver overlay fallback was tested with a camera stream that produced an HLS URL but failed decoder playback; the snapshot preview remained visible with a small fallback message instead of a black box.
- MJPEG, WebRTC, stream profile selection, and transcoding remain future capabilities.

---

# Phase 8: Receiver Entities and Diagnostics ✅

Status: Complete in `0.25.0`.

## Goal

Make each Android TV receiver visible and manageable from Home Assistant.

## Entities

Possible entities:

```txt
sensor.receiver_status
binary_sensor.receiver_connected
button.receiver_test
button.receiver_close
```

Initial implementation:

- Adds one status sensor per receiver.
- Adds one connected binary sensor per receiver.
- Adds test and close buttons per receiver.
- Adds config entry diagnostics with token and stream URL redaction.

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

## Completion Notes

- Completed and tested in Home Assistant with the paired receiver device.
- Receiver status and connected entities are visible on the receiver device page.
- Test and close buttons are available for quick receiver checks.
- Config entry diagnostics include receiver status while redacting pairing tokens and active stream URLs.
- Stage 8 extension completed receiver management controls.
- Android launcher entry moved to an activity alias so the icon can be hidden without disabling the receiver UI itself.
- Authenticated local endpoints added for opening the receiver UI and showing or hiding the launcher icon.
- Home Assistant exposes PiP controls separately from launcher controls where Home Assistant supports config entity grouping.
- Home Assistant exposes a Hide Launcher switch and Open Launcher button.
- Android boot and package-replaced receivers request local control service startup so paired commands can work after restart without manually opening the app.
- Users can recover access without ADB through Home Assistant's Open Launcher control or Android Settings > Apps > HA TV PiP.

---

# Phase 9: Remote Access

Status: Complete in `0.27.0`.

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
- Keep the Home Assistant integration local-first and avoid presenting HA TV PiP as a cloud service.

## Initial Implementation

- Home Assistant registers an optional WebSocket command for outbound receiver registration.
- Remote receivers authenticate to Home Assistant with a normal Home Assistant long-lived access token.
- Remote receivers also register with the existing receiver pairing token, so remote mode stays tied to the paired receiver model.
- `ha_tv_pip.show_camera` and `ha_tv_pip.show_snapshot` prefer an active remote receiver connection and fall back to local HTTP when no remote connection is present.
- Remote receiver commands use the same `show` payload as the local `/show` endpoint.
- Camera stream and snapshot URLs prefer Home Assistant's external URL when a remote receiver connection is active.
- Android TV includes a minimal remote receiver settings panel for Home Assistant external URL and long-lived access token.
- Android TV `/status` reports remote connection state for diagnostics.

## Non-Goal

HA TV PiP should not become a hosted cloud relay. Remote mode uses the user's own Home Assistant external URL or Nabu Casa URL as the endpoint.

## Success Criteria

- A remote Android TV device can connect back to Home Assistant.
- No router port forwarding is required.
- Local mode remains available and preferred when on the same LAN.
- Home Assistant continues to classify the integration as local-first rather than cloud-owned infrastructure.

## Completion Notes

- Implemented and tested the first remote receiver transport slice.
- Android TV can connect outbound to the user's own Home Assistant WebSocket API.
- Home Assistant can register authenticated remote receivers by matching the existing receiver pairing token.
- `ha_tv_pip.show_camera` and `ha_tv_pip.show_snapshot` use the remote WebSocket connection when present and local HTTP otherwise.
- Remote stream and snapshot URLs use Home Assistant's external URL.
- `/status` reports remote receiver state for diagnostics.
- Documentation explicitly describes remote mode as user-owned Home Assistant connectivity, not a hosted HA TV PiP cloud service.

---

# Phase 10: App Store / Distribution Polish

## Goal

Make the app and integration easy for normal Home Assistant users to install.

This is also the main translation implementation pass. Tier 1 languages should be completed before broad release; Tier 2 and Tier 3 languages can follow later.

## Android TV App

- Redesign the main screen as a TV-first receiver dashboard.
- Separate primary PiP controls, launcher controls, remote receiver settings, and diagnostics.
- Make D-pad focus and scrolling predictable on 1080p and 4K TVs.
- Keep verbose endpoint, discovery, and compatibility data in a diagnostics area instead of the top of the screen.
- Prepare Play Store release.
- Add app icon and banner.
- Add onboarding screen.
- Add pairing screen.
- Add troubleshooting screen.
- Simplify remote receiver setup so normal users do not need to type long URLs or long-lived tokens with a TV remote.
- Treat manual remote receiver token entry as an advanced fallback, not the target setup UX.
- Move user-facing strings into Android resources.
- Add Tier 1 Android translations.
- Add privacy-friendly messaging.
- Add crash-safe logging.

## Initial Android UX Polish

- Main receiver screen now starts with app state and primary PiP controls instead of raw diagnostics.
- Receiver health is summarized in TV-readable status cards.
- Pairing, launcher controls, remote receiver settings, and diagnostics are split into separate sections.
- Remote receiver token entry is masked on screen.

## Remote Setup Direction

Remote setup should become Home Assistant-assisted after local pairing.

Preferred direction:

- Home Assistant discovers and pairs the receiver locally.
- The integration detects the user's external Home Assistant URL where available.
- Home Assistant provisions remote receiver settings over the authenticated local receiver connection.
- Users should not need to type long URLs or access tokens on the TV for the normal path.
- If Home Assistant authentication cannot safely be provisioned, keep manual setup available under advanced troubleshooting only.

## Home Assistant Integration

- Prepare for HACS distribution.
- Work toward official Home Assistant integration readiness.
- Add documentation.
- Add example automations.
- Add diagnostics.
- Expand Home Assistant translation files.
- Add Tier 1 Home Assistant translations.
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
- FAQ section.
- Translation planning section.
- Tier 1 website translation content.
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
- Website includes FAQ and translation planning content.
- Tier 1 translations are in place before broad release.

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
