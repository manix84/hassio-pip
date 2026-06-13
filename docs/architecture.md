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
- HACS distribution.
- Play Store distribution.
- WebRTC support.
- Snapshot support.
- Overlay and notification support.

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
- Rendering overlays.

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

Planned services:

```txt
ha_tv_pip.show_camera
ha_tv_pip.show_snapshot
ha_tv_pip.close
ha_tv_pip.test_receiver
```

Future services may include:

```txt
ha_tv_pip.show_message
ha_tv_pip.show_notification
ha_tv_pip.show_dashboard
```

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

Future enhancement.

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

# Current Phase Status

## Implemented

Phase 1 currently implements:

- Android TV application
- Media3 playback
- Public HLS playback
- Picture-in-Picture support
- Basic logging

## Planned

Future phases will add:

- Local control endpoint
- Discovery
- Pairing
- Home Assistant integration
- Camera support
- Snapshot support
- Remote operation
- HACS distribution
- Play Store release
