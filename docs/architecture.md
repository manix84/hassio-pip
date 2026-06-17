# Architecture

## Overview

HA TV PiP is a local-first Home Assistant companion system that allows Home Assistant automations to display camera feeds, snapshots, and alerts on Android TV and Google TV devices using Picture-in-Picture (PiP) playback.

The project consists of three independently deployable components:

```txt
ha-tv-pip/
├── android-tv-app/
│
├── ha-integration/
│
├── website/
│
├── docs/
│
└── examples/
```

The Android TV application acts as a receiver.

The Home Assistant integration acts as a controller.

The promotional website acts as the public landing page and documentation entry point.

The overall design philosophy is:

```txt
Home Assistant decides WHAT to display.
Android TV decides HOW to display it.
```

This separation allows playback behaviour to evolve independently from Home Assistant integration logic.

---

# Design Goals

## Primary Goals

- Local-first operation.
- Minimal configuration.
- Automatic device discovery.
- Secure pairing.
- Reliable Picture-in-Picture playback.
- Home Assistant native experience.
- Support multiple Android TV devices.
- Support multiple camera types.
- Graceful fallback when streaming fails.

## Secondary Goals

- Remote receiver support.
- Internationalization across Android, Home Assistant, and website.
- HACS distribution.
- Long-term official Home Assistant integration readiness.
- Play Store distribution.
- WebRTC support.
- Snapshot support.
- Overlay and notification support.
- Future Fire TV / Vega OS receiver support.
- Exploratory Apple TV / tvOS receiver support.

## Non-Goals

The project is not intended to:

- Replace Home Assistant dashboards.
- Replace Android TV launchers.
- Provide NVR functionality.
- Manage camera recording.
- Perform video transcoding.

---

# System Architecture

Target architecture:

```txt
┌─────────────────────┐
│   Home Assistant    │
└──────────┬──────────┘
           │
           │ Service Calls
           │
┌──────────▼──────────┐
│ HA TV PiP           │
│ Integration         │
└──────────┬──────────┘
           │
           │ Commands
           │
┌──────────▼──────────┐
│ Android TV Receiver │
│ App                 │
└──────────┬──────────┘
           │
           │ Playback
           │
┌──────────▼──────────┐
│ Camera Stream       │
│ Snapshot            │
│ HLS                 │
│ WebRTC              │
└─────────────────────┘
```

Home Assistant should never directly control Android TV playback behaviour.

Instead, it sends high-level commands:

```txt
Show Camera
Show Snapshot
Close Display
Test Receiver
```

The Android TV app is responsible for:

- Opening playback.
- Entering PiP.
- Managing playback lifecycle.
- Recovering from playback errors.
- Closing displays.
- Rendering overlays when native Android TV PiP is unavailable.
- Serving the local Stage 2 receiver control endpoint.

---

# Repository Structure

```txt
ha-tv-pip/
├── android-tv-app/
│   Android TV application
│
├── ha-integration/
│   Home Assistant custom integration
│
├── website/
│   Promotional website and project landing page
│
├── docs/
│   Project documentation
│
├── examples/
│   Example automations
│
└── README.md
```

The repository is intentionally structured as a monorepo.

All projects should share documentation and release planning while remaining independently deployable.

---

# Android TV Application

## Responsibilities

The Android TV application is responsible for:

- Video playback.
- Snapshot rendering.
- PiP management.
- Device discovery advertisement.
- Pairing UI.
- Local control endpoint.
- Remote connection handling.
- Diagnostics.

The Android TV application should remain unaware of Home Assistant internals.

It should only understand generic commands.

Example:

```json
{
  "action": "show",
  "title": "Front Door",
  "streamType": "hls",
  "url": "https://..."
}
```

This keeps the receiver reusable and loosely coupled.

Future receiver apps for Fire TV, Vega OS, or Apple TV should use the same high-level command model where possible. Platform-specific display behavior should stay inside each receiver implementation.

---

## Internal Components

Target internal architecture:

```txt
Android TV App
│
├── UI Layer
│   ├── MainActivity
│   ├── PlayerActivity
│   ├── PairingActivity
│   └── SettingsActivity
│
├── Playback Layer
│   ├── Media3 Player
│   ├── PiP Manager
│   └── Stream Resolver
│
├── Receiver Layer
│   ├── HTTP Endpoint
│   ├── WebSocket Client
│   └── Command Dispatcher
│
├── Discovery Layer
│   └── mDNS / NSD
│
└── Storage Layer
    ├── Device Settings
    ├── Pairing Tokens
    └── Diagnostics
```

Each layer should remain independently testable.

---

# Home Assistant Integration

## Responsibilities

The Home Assistant integration is responsible for:

- Device discovery.
- Device registration.
- Pairing workflows.
- Configuration flows.
- Service registration.
- Camera resolution.
- Stream selection.
- Diagnostics.

The integration should never be responsible for media playback.

---

## Home Assistant Services

Initial service:

```txt
ha_tv_pip.show_camera
```

The Stage 5 service resolves Home Assistant camera HLS URLs and sends authenticated `/show` commands to paired receivers. It uses Home Assistant's standard `target.device_id` selector, filtered to HA TV PiP receiver devices.

Implemented receiver display services include `ha_tv_pip.show_camera`, `ha_tv_pip.show_snapshot`, and `ha_tv_pip.show_notification`. Camera and snapshot commands can also carry optional notification presentation fields for title/message footers.

Enhanced notification fields are inspired by existing Android TV notification popup tools while using explicit wire names:

```json
{
  "streamType": "notification",
  "position": "top_right",
  "title": "Home Assistant",
  "titleColor": "#50BFF2",
  "titleSize": 24,
  "message": "",
  "messageColor": "#fbf5f5",
  "messageSize": 18,
  "backgroundColor": "#B30F0E0E",
  "width": 512,
  "height": 240
}
```

The receiver protocol validates colors, clamps text sizes to TV-readable ranges, maps position values to explicit screen corners, and keeps these fields optional so camera, snapshot, and notification commands work with sensible defaults. Media popups use an explicit `showNotification` flag for title/message footers; width and height can resize media without forcing text to appear.

---

## Device Model

Each paired Android TV should appear as a Home Assistant device.

Example:

```txt
Living Room TV
├── Connected
├── Last Seen
├── App Version
├── Playback State
└── Diagnostics
```

This allows users to manage multiple receivers independently.

---

# Promotional Website

## Responsibilities

The promotional website is responsible for:

- Explaining the project clearly.
- Showing current project status.
- Linking to roadmap, architecture, development docs, releases, and license.
- Promoting the Android TV app and Home Assistant integration.
- Preparing for future GitHub Pages deployment.

The website should remain static.

It should not:

- Generate releases.
- Require authentication.
- Include analytics by default.
- Act as a backend or control plane.

---

# Discovery Architecture

Discovery should use mDNS / Zeroconf.

Receiver advertises:

```txt
_ha-tv-pip._tcp.local
```

Discovery metadata:

```txt
device_id
device_name
version
api_version
pairing_state
```

Home Assistant should automatically detect receivers and offer configuration.

IP addresses should be treated as dynamic.

The integration should identify receivers using a stable device identifier.

---

# Pairing Architecture

The system should use explicit pairing.

Target flow:

```txt
Home Assistant
    │
    ▼
Discover Receiver
    │
    ▼
Start Pairing
    │
    ▼
TV Shows Pairing Code
    │
    ▼
User Confirms
    │
    ▼
Shared Token Created
```

After pairing:

- Commands require authentication.
- Pairing tokens are stored securely.
- Receivers can be unpaired independently.

---

# Streaming Architecture

Supported stream types:

```txt
snapshot
hls
mjpeg
webrtc
```

Preferred order:

```txt
1. WebRTC
2. HLS
3. MJPEG
4. Snapshot
```

Actual implementation order:

```txt
1. HLS
2. Snapshot
3. MJPEG
4. WebRTC
```

The Home Assistant integration is responsible for selecting the most appropriate stream type.
Future versions should understand receiver playback capabilities and camera stream profiles so unsupported main streams can fall back to a compatible profile, restreaming path, or transcoding path.

The Android TV app is responsible for rendering it.

---

# Local and Remote Operation

## Local Mode

Preferred mode.

```txt
Home Assistant
      │
      ▼
Android TV Receiver
```

Benefits:

- Lowest latency.
- Simplest architecture.
- No external dependencies.

---

## Remote Mode

Optional Phase 9 transport.

```txt
Android TV
      │
      ▼
Home Assistant External URL
      │
      ▼
Commands
```

Remote receivers should connect outbound to Home Assistant.

Home Assistant should never require inbound access to remote TVs.

Remote mode does not introduce a HA TV PiP cloud service. The receiver connects to the user's own Home Assistant external URL, including a Nabu Casa URL if the user already uses Home Assistant Cloud. The Home Assistant integration remains local-first and keeps `iot_class: local_push`.

Remote command flow:

```txt
Android TV receiver
    │ 1. Authenticates to Home Assistant WebSocket API
    │ 2. Registers with existing receiver pairing token
    ▼
Home Assistant integration
    │ 3. Stores the active outbound connection in memory
    │ 4. Sends show commands over WebSocket when remote is connected
    ▼
Android TV receiver playback
```

When a remote receiver is connected, Home Assistant should resolve camera streams and snapshots against the external Home Assistant URL. When no remote receiver is connected, local HTTP control remains the fallback.

---

# Diagnostics

Both components should expose diagnostics.

Android TV diagnostics:

```txt
Version
Device ID
Last Command
Playback State
Connection Status
Last Error
```

Home Assistant diagnostics:

```txt
Receiver Status
Pairing Status
Stream Type
Last Command
Last Error
```

The goal is to allow troubleshooting without requiring users to inspect source code or application logs.

---

# Internationalization

English is the source language.

The Android TV app should use Android string resources for user-facing UI.

The Home Assistant integration should use `strings.json` and `translations/*.json`.

The website should use lightweight static locale content and routes when translation work starts.

Translation implementation belongs to the Phase 10 polish pass. Tier 1 languages from `docs/translations.md` are complete for the current Android, Home Assistant, and website surfaces. Tier 2 and Tier 3 languages are planned after beta hardening and broader testing.

---

# Current Phase Status

## Implemented

Phase 1 currently implements:

- Android TV application
- Media3 playback
- Public HLS playback
- Native Picture-in-Picture support where Android TV exposes it
- Floating overlay fallback for devices that reject native PiP
- Basic logging

Phase 2 currently adds:

- Local HTTP status endpoint
- Local HLS show command
- Local close command
- Runtime playback state reporting
- API metadata and JSON error responses
- Receiver capability metadata for supported command types, notification positions, preview images, playable fallbacks, overlay fallback, pairing, launcher management, and remote receiver settings
- Home Assistant status parsing for receiver capabilities so automations, diagnostics, and future UI paths can reason about installed receiver features

Phase 3 currently adds:

- Android NSD / mDNS advertisement for `_ha-tv-pip._tcp.local.`
- Discovery metadata for device id, name, version, pairing state, and API version
- Discovery runtime state in the Android app status endpoint and main screen
- Home Assistant integration manifest Zeroconf matching
- Home Assistant config flow creation from discovered receiver metadata

Phase 4 currently adds:

- TV-visible pairing code flow
- Local bearer-token authentication for receiver control commands
- Home Assistant config-flow pairing and token storage
- Pairing reset from the Android TV app
- Discovery metadata refresh when pairing state changes

Phase 5 currently adds:

- `ha_tv_pip.show_camera` Home Assistant service
- Paired receiver targeting with Home Assistant `target.device_id`
- Home Assistant HLS camera stream resolution
- Authenticated receiver `/show` calls
- Receiver-side stream error reporting for unsupported codecs or profiles

Phase 6 currently adds:

- `ha_tv_pip.show_snapshot` Home Assistant service
- Camera proxy snapshot URL resolution
- Android TV snapshot overlay rendering
- Shared pairing, bearer-token auth, receiver targeting, and duration timeouts for snapshots
- Optional entity-based snapshot previews while video streams load

Phase 7 currently adds:

- `stream_type: auto`, `stream_type: hls`, `stream_type: mjpeg`, `stream_type: mjpeg_first`, and `stream_type: snapshot` for `ha_tv_pip.show_camera`
- Optional `stream_camera_entity` support for selecting a separate Android TV-compatible live stream entity
- Receiver-side MJPEG overlay rendering for Home Assistant camera proxy streams
- Home Assistant-side fallback from HLS to MJPEG, then snapshot, when stream URL resolution fails
- Receiver-side playable fallback from accepted HLS playback to MJPEG when the Android decoder rejects the HLS stream and a fallback stream was provided
- Receiver-side snapshot preview fallback when no playable fallback is available or the playable fallback also fails
- Stream type selection logging before receiver commands are sent

## Planned

Future phases will add:

- Receiver entities and diagnostics
- WebRTC stream mode
- Stream profile selection or transcoding
- Remote operation
- HACS distribution
- Official Home Assistant integration readiness
- Play Store release
