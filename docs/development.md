# Development

This document describes the development workflow, repository structure, coding standards, tooling, and project conventions used throughout HA TV PiP.

The goal is to keep development approachable for contributors while providing enough structure for future growth.

---

# Repository Layout

```txt
ha-tv-pip/
│
├── android-tv-app/
│   Android TV receiver application
│
├── ha-integration/
│   Home Assistant custom integration
│
├── docs/
│   Project documentation
│
├── examples/
│   Example Home Assistant automations
│
├── .github/
│   CI/CD workflows
│
├── README.md
├── LICENSE
└── .gitignore
```

The repository is intentionally structured as a monorepo.

The Android TV application and Home Assistant integration should remain independently buildable and deployable.

---

# Development Philosophy

The project follows a few core principles:

## Local First

Features should work locally before remote functionality is added.

Preferred order:

```txt
Local Playback
→ Local Control
→ Discovery
→ Pairing
→ Home Assistant Integration
→ Remote Connectivity
```

Avoid introducing cloud dependencies unless they solve a specific problem.

---

## Build Vertical Slices

Features should be implemented as complete end-to-end slices.

Good:

```txt
Home Assistant
    ↓
Show Camera
    ↓
Android TV
    ↓
PiP Playback
```

Bad:

```txt
Build half the pairing system
Build half the discovery system
Build half the streaming system
```

Every phase should produce something demonstrably useful.

---

## Keep Components Loosely Coupled

The Android TV application should not depend on Home Assistant internals.

The Home Assistant integration should not depend on Android UI behaviour.

Communication should occur through stable APIs and command payloads.

---

# Development Environment

## Recommended Tools

### Primary Editor

```txt
VSCode
```

Recommended extensions:

```txt
GitHub Copilot / Codex
EditorConfig
Markdown All In One
Error Lens
GitLens
```

---

### Android Development

```txt
Android Studio
```

Android Studio should be used for:

- Android SDK management
- Emulator management
- Device debugging
- APK signing
- Release builds
- Android profiling

VSCode remains the preferred daily development environment.

Common repo scripts:

```sh
npm run check
npm run android:assemble
npm run android:lint
npm run android:clean
```

The root `package.json` is the monorepo version source. Android app version metadata should stay aligned with it.

---

### Home Assistant Development

Recommended:

```txt
Docker
VSCode
Home Assistant Development Container
```

Future integration development should follow Home Assistant development best practices.

---

# Android TV Application

## Technology Stack

```txt
Kotlin
Jetpack Compose
Media3
Gradle Kotlin DSL
Android TV APIs
```

---

## Architectural Goals

The Android TV application should evolve toward:

```txt
UI Layer
    ↓
Playback Layer
    ↓
Command Layer
    ↓
Discovery Layer
    ↓
Storage Layer
```

Avoid placing networking, playback, and UI logic inside Activities.

Activities should remain thin.

---

## Future Package Structure

Suggested direction:

```txt
app/src/main/java/com/hatvpip/
│
├── ui/
│
├── playback/
│
├── receiver/
│
├── discovery/
│
├── pairing/
│
├── diagnostics/
│
├── models/
│
└── storage/
```

Exact implementation may evolve over time.

---

## Logging

Prefer structured logging.

Example:

```txt
[Playback]
[PiP]
[Discovery]
[Pairing]
[Receiver]
```

Avoid generic log messages.

Good:

```txt
[Playback] HLS stream started.
```

Bad:

```txt
Something happened.
```

---

## Error Handling

Failures should:

1. Be logged.
2. Be recoverable where possible.
3. Present useful information to developers.

Avoid silent failures.

---

# Home Assistant Integration

## Current Status

Not implemented during Phase 1.

Placeholder files exist under:

```txt
ha-integration/custom_components/ha_tv_pip/
```

---

## Planned Technology

```txt
Python
Home Assistant Config Flow
Zeroconf Discovery
Device Registry
Entity Registry
Service Registry
```

---

## Integration Responsibilities

The integration will eventually:

- Discover receivers.
- Pair receivers.
- Register devices.
- Expose services.
- Resolve camera streams.
- Provide diagnostics.

The integration should not be responsible for playback.

---

# Communication Model

Future communication between Home Assistant and receivers should use command payloads.

Example:

```json
{
  "action": "show",
  "title": "Front Door",
  "streamType": "hls",
  "url": "https://example.com/stream.m3u8",
  "durationSeconds": 30,
  "enterPip": true
}
```

This contract should remain stable as the project grows.

---

# Branch Strategy

Suggested workflow:

```txt
main
│
├── feature/android-pip
├── feature/discovery
├── feature/pairing
├── feature/ha-integration
└── feature/remote-access
```

Rules:

- Never commit directly to main.
- Merge through pull requests.
- Keep feature branches focused.

---

# Testing Strategy

## Phase 1

Manual testing is acceptable.

Test on:

```txt
Android TV Emulator
Google TV
Physical Android TV
```

Focus on:

- Playback reliability
- PiP behaviour
- Lifecycle handling
- Crash recovery

---

## Future Testing

Add:

```txt
Unit Tests
Integration Tests
Discovery Tests
Pairing Tests
Home Assistant Service Tests
```

---

# Continuous Integration

Future GitHub Actions should provide:

```txt
Android Build Validation
Linting
Static Analysis
Home Assistant Validation
Documentation Checks
```

Pull requests should pass automated validation before merging.

---

# Documentation Requirements

When adding significant functionality:

Update:

```txt
README.md
docs/roadmap.md
docs/architecture.md
docs/development.md
```

Documentation should evolve alongside the codebase.

---

# Codex Development Guidelines

When implementing features:

1. Follow the roadmap.
2. Do not skip phases.
3. Prefer the simplest working implementation.
4. Avoid introducing unnecessary dependencies.
5. Keep Android-specific logic isolated.
6. Keep Home Assistant-specific logic isolated.
7. Leave clear extension points for future phases.
8. Prioritise maintainability over cleverness.

When uncertain:

Choose the simplest implementation that supports future expansion.

---

# Current Phase

Current development target:

```txt
Phase 1
Android TV PiP MVP
```

Success criteria:

```txt
Play a test HLS stream.
Enter PiP mode.
Remain stable across lifecycle events.
Provide a foundation for future receiver control.
```

No Home Assistant functionality should be implemented until Phase 1 is complete and stable.
