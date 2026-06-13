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
├── website/
│   Promotional website
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

The Android TV application, Home Assistant integration, and website should remain independently buildable and deployable.

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
npm run android:assemble:release
npm run android:lint
npm run android:clean
npm run package:integration
npm run website:dev
npm run website:build
npm run website:preview
```

### Website Development

```txt
Vite
React
TypeScript
SCSS Modules
```

The website lives in:

```txt
website/
```

Run locally:

```sh
npm run website:dev
```

Build locally:

```sh
npm run website:build
```

Preview a built site:

```sh
npm run website:preview
```

The website is a static promotional landing page. It should not contain a backend, analytics, authentication, or release generation logic.

The root `package.json` is the monorepo version source. Android app version metadata should stay aligned with it.

---

# Versioning and Releases 📦

## Version Source

The root `package.json` version is the source of truth for the monorepo.

Files that should stay aligned:

- Root `package.json`.
- `android-tv-app/package.json`.
- `website/package.json`.
- Android `versionName` in `android-tv-app/app/build.gradle.kts`.
- Home Assistant `manifest.json` version once the integration is implemented.

Check version consistency with:

```sh
npm run version:check
```

During Phase 1, the Home Assistant integration is only a placeholder. The version check warns when `ha-integration/custom_components/ha_tv_pip/manifest.json` does not exist instead of failing.

## Pre-Commit Version Bumps 🔢

The repo uses a Husky pre-commit hook to keep runtime commits versioned automatically.

The hook runs:

```sh
npm run version:precommit
```

The root `package.json` version remains the source of truth. When a bump happens, the hook syncs:

- `package.json`
- `package-lock.json`, if present
- `android-tv-app/package.json`
- `website/package.json`
- Android `versionName` in `android-tv-app/app/build.gradle.kts`
- Home Assistant `manifest.json`, once it exists

### PATCH Bumps 🩹

PATCH bumps are automatic for normal runtime implementation changes under:

```txt
android-tv-app/app/src/
android-tv-app/src/
android-tv-app/build.gradle.kts
android-tv-app/settings.gradle.kts
ha-integration/custom_components/ha_tv_pip/
```

Example:

```txt
0.2.4 -> 0.2.5
```

### MINOR Bumps 🚦

MINOR bumps are best-effort and are used for likely API, protocol, discovery, pairing, service schema, or compatibility changes.

Explicit markers in staged diffs trigger MINOR:

```txt
[minor]
[api]
[breaking]
[protocol]
[service-schema]
[pairing]
[discovery]
[compatibility]
```

Likely contract files also trigger MINOR:

```txt
ha-integration/custom_components/ha_tv_pip/services.yaml
ha-integration/custom_components/ha_tv_pip/config_flow.py
ha-integration/custom_components/ha_tv_pip/manifest.json
ha-integration/custom_components/ha_tv_pip/const.py
android-tv-app/app/src/**/models/**
android-tv-app/app/src/**/receiver/**
android-tv-app/app/src/**/pairing/**
android-tv-app/app/src/**/discovery/**
android-tv-app/app/src/**/api/**
```

When MINOR is bumped, PATCH resets to `0`:

```txt
0.2.4 -> 0.3.0
```

### MAJOR Protection 🛡️

MAJOR bumps are never automatic.

Use MAJOR only for extreme changes such as a complete rewrite, incompatible architecture replacement, or abandoning the existing receiver protocol.

To force a MAJOR bump:

```sh
VERSION_BUMP=major ALLOW_MAJOR_BUMP=true git commit -m "Rewrite receiver architecture"
```

Without `ALLOW_MAJOR_BUMP=true`, the hook fails clearly.

### No Version Bump 🧘

Support-only changes do not bump versions:

```txt
docs/
examples/
scripts/
.github/
README.md
LICENSE
.gitignore
package.json-only metadata changes
release packaging scripts
documentation-only changes
```

The hook also skips when only version files are staged, which avoids bump loops after a failed commit retry.

### Manual Overrides 🎛️

Use `VERSION_BUMP` when the automatic decision needs help:

```sh
VERSION_BUMP=minor git commit -m "Update receiver command payload"
VERSION_BUMP=patch git commit -m "Fix playback lifecycle"
VERSION_BUMP=none git commit -m "Update docs"
VERSION_BUMP=major ALLOW_MAJOR_BUMP=true git commit -m "Rewrite architecture"
```

Allowed values:

```txt
auto
none
patch
minor
major
```

If unset, the hook behaves as `VERSION_BUMP=auto`.

### Manual Version Bump Commands 🛠️

You can bump versions without committing:

```sh
npm run version:patch
npm run version:minor
ALLOW_MAJOR_BUMP=true npm run version:major
```

### Emergency Bypass 🚨

Bypass hooks only when necessary:

```sh
git commit --no-verify
```

Bypassing hooks should be rare. Run `npm run version:check` afterward when possible.

## Android Local Build

Build the debug APK:

```sh
npm run android:assemble
```

Build the release APK:

```sh
npm run android:assemble:release
```

The release build currently produces an unsigned APK. Play Store deployment and signing automation are intentionally out of scope.

## Integration Local Packaging

Package the Home Assistant integration:

```sh
npm run package:integration
```

This creates:

```txt
dist/ha-tv-pip-integration-vX.Y.Z.zip
```

The zip preserves the Home Assistant install path:

```txt
custom_components/ha_tv_pip/
```

It does not include the monorepo wrapper path `ha-integration/custom_components/ha_tv_pip/`.

## GitHub Release Assets

When a GitHub Release is published, `.github/workflows/release.yml`:

1. Checks out the repo.
2. Sets up Java, Android SDK, Gradle, and Node.
3. Reads the release version from root `package.json`.
4. Runs the version consistency check.
5. Builds the Android release APK.
6. Packages the Home Assistant integration zip.
7. Uploads both files to the GitHub Release.

For version `1.2.3`, expected release assets are:

```txt
ha-tv-pip-android-v1.2.3.apk
ha-tv-pip-integration-v1.2.3.zip
```

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
