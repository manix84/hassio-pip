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

Translation planning lives in:

```txt
docs/translations.md
```

New user-facing strings should be designed with translation in mind even before translated files exist. The main translation implementation pass is planned for Phase 10 distribution polish.

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
npm run install:all
npm run check
npm run lint
npm run typecheck
npm run test
npm run android:assemble
npm run android:assemble:release
npm run android:build:dry-run
npm run android:lint
npm run android:test
npm run android:typecheck
npm run ha:build:dry-run
npm run ha:lint
npm run ha:test
npm run ha:typecheck
npm run android:clean
npm run package:integration
npm run website:dev
npm run website:build
npm run website:build:dry-run
npm run website:lint
npm run website:test
npm run website:typecheck
npm run website:preview
```

## Quality Checks ✅

The monorepo exposes shared quality commands from the root:

```sh
npm run lint
npm run typecheck
npm run test
npm run check
```

`npm run check` runs version consistency, linting, type checking, and tests.

Project-specific quality commands:

```sh
npm run android:lint
npm run android:test
npm run android:typecheck
npm run ha:lint
npm run ha:test
npm run ha:typecheck
npm run website:lint
npm run website:test
npm run website:typecheck
npm run android:build:dry-run
npm run ha:build:dry-run
npm run website:build:dry-run
```

Quality tooling by area:

- Android TV app: Android Gradle Plugin lint, JVM unit tests, and Kotlin debug compilation.
- Home Assistant integration: Ruff, pytest, and MyPy against the custom integration package.
- Website: ESLint for React/TypeScript, Vitest, and `tsc --noEmit` for type checking.

Dry-run builds by area:

- Android TV app: assembles the debug APK.
- Home Assistant integration: packages the custom integration zip from `custom_components/ha_tv_pip/`.
- Website: runs the Vite production build.

GitHub Actions runs project-specific quality workflows for the Android TV app, Home Assistant integration, and website. Each workflow still exposes separate jobs, such as `website: lint`, `website: test`, `website: typecheck`, and `website: build dry-run`. The Website Deploy workflow only builds/deploys the site, and the Release workflow only packages release assets.

Install Home Assistant integration dev tools with:

```sh
npm run install:all
```

The install script creates `ha-integration/.venv/` and installs Python dev tools there, so Homebrew-managed Python installations are not modified.

Install website dependencies with:

```sh
npm --prefix website install
```

Install all project dependencies from the root with:

```sh
npm run install:all
```

The install script covers root npm metadata, Android app npm metadata, website npm dependencies, and Home Assistant integration Python dev tools. Android Gradle dependencies are still resolved by Android Studio or Gradle during Android builds.

For Android builds, the install script writes `android-tv-app/local.properties` when it can find an SDK through `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or the usual Android Studio SDK locations. If no SDK is installed yet, install it through Android Studio and rerun `npm run install:all`.

## Pairing Development 🔐

Stage 4 secures the local receiver API with one-time pairing and bearer-token requests.

The Android TV receiver exposes:

```txt
POST /pair/start
POST /pair/confirm
```

`/pair/start` opens a short pairing window and shows the code on the TV screen only. The HTTP response deliberately does not include the code, so LAN clients must have access to the TV display to pair.

After `/pair/confirm` succeeds, `/show` and `/close` require:

```txt
Authorization: Bearer <token>
```

Use `Reset Pairing` in the Android TV app before testing a new Home Assistant pairing flow. Existing pairings cannot be replaced remotely.

## Receiver Management Development 🧰

Stage 8 also includes receiver management controls exposed through Home Assistant.

The Android receiver exposes authenticated endpoints for paired clients:

```txt
POST /management/open
POST /management/launcher
```

`/management/open` reopens the receiver UI on the TV.

`/management/launcher` accepts:

```json
{
  "visible": true
}
```

Home Assistant represents this as:

- PiP controls: `Test PiP`, `Close PiP`
- Launcher controls: `Hide Launcher`, `Open Launcher`

Launcher controls are marked as Home Assistant config entities so they are visually separated from day-to-day PiP controls where Home Assistant supports that grouping.

If the launcher icon is hidden, users can recover through Home Assistant's Open Launcher control or Android Settings > Apps > HA TV PiP. The Android app registers boot and package-replaced receivers so the local control service can start after restart without manually opening the app first.

## Remote Receiver Development 🌍

Phase 9 adds optional outbound remote receiver transport.

The design remains local-first:

- HA TV PiP does not provide a hosted cloud relay.
- The Home Assistant integration remains `iot_class: local_push`.
- Remote receivers connect to the user's own Home Assistant external URL.
- Nabu Casa URLs are supported as Home Assistant external URLs, not as a HA TV PiP cloud dependency.
- Local HTTP control remains the fallback when no remote receiver connection is active.

Home Assistant registers this WebSocket command for receiver registration:

```txt
ha_tv_pip/receiver/register
```

Receiver registration payload:

```json
{
  "type": "ha_tv_pip/receiver/register",
  "device_id": "49e3b07d8f4b7d65",
  "name": "Travel TV",
  "token": "receiver-pairing-token"
}
```

The WebSocket itself is authenticated with a normal Home Assistant long-lived access token. The `token` field above is the existing HA TV PiP receiver pairing token, used to prove the remote connection belongs to a configured receiver.

Remote receiver commands are pushed as Home Assistant WebSocket event messages:

```json
{
  "type": "event",
  "event": {
    "event_type": "ha_tv_pip/receiver_command",
    "data": {
      "command": "show",
      "payload": {
        "title": "Front Door",
        "url": "https://example.test/api/hls/front-door",
        "streamType": "hls",
        "enterPip": true
      }
    }
  }
}
```

When a receiver is connected remotely, service handlers prefer Home Assistant's external URL for HLS streams and snapshot URLs. When the receiver is local-only, they continue to prefer the local URL.

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

The website workflow builds on pull requests and deploys `website/dist` to GitHub Pages on pushes to `main`.

The root `package.json` is the monorepo version source. Android app version metadata should stay aligned with it.

---

# Versioning and Releases 📦

## Version Source

The root `package.json` version is the source of truth for the monorepo.

Files that should stay aligned:

- Root `package.json`.
- Root `package-lock.json`, if present.
- `android-tv-app/package.json`.
- `ha-integration/package.json`.
- `website/package.json`.
- `website/package-lock.json`, if present.
- Android `versionName` in `android-tv-app/app/build.gradle.kts`.
- Home Assistant `manifest.json` version.

Check version consistency with:

```sh
npm run version:check
```

The Home Assistant integration manifest version is kept in sync with the root package version.

## Pre-Commit Version Bumps 🔢

The repo uses a native Git pre-commit hook to keep runtime commits versioned automatically.

Install the hook path after cloning:

```sh
npm run hooks:install
```

`npm install` also runs the same setup through the root `prepare` script.

The hook runs:

```sh
npm run version:precommit
npm run test
```

The root `package.json` version remains the source of truth. When a bump happens, the hook syncs:

- `package.json`
- `package-lock.json`, if present
- `android-tv-app/package.json`
- `ha-integration/package.json`
- `website/package.json`
- `website/package-lock.json`, if present
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

Build the release Android App Bundle:

```sh
npm run android:bundle:release
```

The release APK and App Bundle are currently unsigned. Play Store deployment and signing automation are intentionally out of scope. Play Store listing, privacy, screenshot, signing, and release-note prep is tracked in `docs/play-store.md`.

## Integration Local Packaging

Package the Home Assistant integration:

```sh
npm run package:integration
```

This creates:

```txt
dist/ha-tv-pip-integration-vX.Y.Z.zip
dist/ha-tv-pip-integration.zip
```

The zip preserves the Home Assistant install path:

```txt
custom_components/ha_tv_pip/
```

It does not include the monorepo wrapper path `ha-integration/custom_components/ha_tv_pip/`.

The versioned zip is the human-readable release asset. The stable `ha-tv-pip-integration.zip` file is the HACS release asset referenced by root `hacs.json`.

## GitHub Release Assets

When code is pushed or merged into `main`, `.github/workflows/release.yml`:

1. Checks out the repo.
2. Sets up Java, Android SDK, Gradle, and Node.
3. Reads the release version from root `package.json`.
4. Runs the version consistency check.
5. Builds the Android debug and release APKs.
6. Packages the Home Assistant integration zip.
7. Creates draft GitHub Release `vX.Y.Z` with the Android APKs, versioned integration zip, and stable HACS integration zip already attached.
8. Publishes the draft GitHub Release.

Published GitHub Releases are treated as immutable. The workflow will not replace assets on an existing published release; it exits cleanly when the release for the current version already exists. Bump the root `package.json` version before producing another release. If an older failed workflow already created a published release without assets, delete that failed release manually or move forward with the next version.

For version `1.2.3`, expected release assets are:

```txt
ha-tv-pip-android-debug-v1.2.3.apk
ha-tv-pip-android-release-v1.2.3.apk
ha-tv-pip-integration-v1.2.3.zip
ha-tv-pip-integration.zip
```

## HACS Distribution

HACS expects custom integration repositories to provide a root `hacs.json` and installable integration content under `custom_components/<domain>/`. Because HA TV PiP is a monorepo, the default branch layout is not directly installable by HACS.

The repo therefore uses root `hacs.json` with:

```json
{
  "name": "HA TV PiP",
  "zip_release": true,
  "filename": "ha-tv-pip-integration.zip",
  "hide_default_branch": true
}
```

The release workflow attaches that stable zip while creating the draft GitHub Release from `main`. Its internal path is:

```txt
custom_components/ha_tv_pip/
```

For custom-repository installs, users should add `https://github.com/manix84/ha-tv-pip` in HACS as category `Integration`.

Default HACS repository inclusion is a separate later step. Before submitting to the HACS default repository list, confirm the public GitHub repository has a description, topics, passing HACS validation, passing Hassfest validation, and at least one full GitHub Release.

## Stage 12 Beta Release Hardening

Stage 12 completed in `0.48.0` as a release-quality pass rather than a feature-expansion pass.

The Stage 12 release-candidate pass used the full repository check:

```sh
npm run check
```

It also built and packaged each project area:

```sh
npm run android:assemble:debug
npm run android:assemble:release
npm run package:integration
npm run website:build
```

Verify release packaging expectations:

- Android debug APK asset: `ha-tv-pip-android-debug-vX.Y.Z.apk`.
- Android release APK asset: `ha-tv-pip-android-release-vX.Y.Z.apk`.
- Versioned integration zip: `ha-tv-pip-integration-vX.Y.Z.zip`.
- Stable HACS integration zip: `ha-tv-pip-integration.zip`.
- Integration zip internal path: `custom_components/ha_tv_pip/`.
- Root `package.json`, Android `versionName`, HA `manifest.json`, and project `package.json` files all match.

Documentation work in Stage 12 included:

- Root README install flow.
- Android TV app install and sideload guidance.
- HACS custom-repository install guidance.
- Manual custom integration fallback guidance.
- Website current status and Stage 11 notification examples.
- Example automations for text-only notifications, camera with footer, snapshot with footer, and resize-only media popups.
- Release notes for the beta candidate.

Stage 12 finished with GitHub Release `v0.48.0` from `main` after local checks, builds, packaging, website build, and docs were clean.

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

Implemented through Stage 6.

The integration currently lives under:

```txt
ha-integration/custom_components/ha_tv_pip/
```

It supports Zeroconf discovery, TV-visible pairing, bearer-token receiver control, `ha_tv_pip.show_camera`, `ha_tv_pip.show_snapshot`, and optional entity-based snapshot previews while video streams load.

---

## Technology

```txt
Python
Home Assistant Config Flow
Zeroconf Discovery
Device Registry
Service Registry
Ruff
Mypy
Pytest
```

---

## Integration Responsibilities

The integration currently:

- Discover receivers.
- Pair receivers.
- Register devices.
- Expose services.
- Resolve camera streams.
- Resolve camera snapshots.
- Send authenticated receiver commands.

Future stages will add:

- Stream profile selection and fallback policy.
- Diagnostics.
- HACS readiness.
- Official Home Assistant integration readiness.

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

Enhanced notifications extend this model with optional presentation fields rather than replacing the existing camera and snapshot command shape:

```json
{
  "showNotification": true,
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

Implementation notes:

- Keep all fields optional and provide readable defaults.
- Validate hex and alpha-hex colors before sending them to Android UI code.
- Send `showNotification: true` for media title/message footers so width/height can resize a popup without forcing footer text.
- Clamp title and message sizes to safe TV-readable ranges.
- Prefer named Home Assistant service options where possible, while still mapping cleanly to the receiver JSON payload.
- Keep `position` documented as a stable corner mapping.

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

## Current Coverage

Automated checks now cover all three project areas:

- Android TV app: Gradle lint, Kotlin compilation, and unit tests.
- Home Assistant integration: Ruff linting, Mypy type checking, and pytest.
- Website: ESLint, TypeScript type checking, and Vitest.

Manual TV testing is still required for receiver behaviour that depends on real Android TV / Google TV system features.

## Device Testing

Test on:

```txt
Android TV Emulator
Google TV
Physical Android TV
```

Focus on:

- Playback reliability
- PiP behaviour
- Overlay fallback behaviour on Google TV devices that do not expose native PiP
- Lifecycle handling
- Crash recovery

---

# Continuous Integration

GitHub Actions currently provides split quality workflows:

```txt
quality-android-tv-app.yml
quality-ha-integration.yml
quality-website.yml
```

Each workflow exposes separate lint, typecheck, test, and dry-run build jobs so PR checks and README badges remain specific.

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
Phase 10
Distribution polish and TV-first setup
```

Phase 10 keeps onboarding, pairing, and troubleshooting inside the main Android TV dashboard for now. Separate screens are deferred until the setup flow becomes large enough to justify deeper navigation.

Phase 1 is complete in `0.4.0`. It validated:

```txt
Play a test HLS stream.
Enter native PiP where supported.
Use the no-ADB overlay fallback where native PiP is unavailable.
Remain stable across lifecycle events.
Provide a foundation for future receiver control.
```

Phase 2 is complete in `0.6.0`. It added local receiver control.

Stage 2 local endpoint testing:

```sh
curl http://ANDROID_TV_IP:8765/status

curl -X POST http://ANDROID_TV_IP:8765/show \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TOKEN' \
  -d '{"title":"Front Door","url":"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8","streamType":"hls","durationSeconds":30,"enterPip":true}'

curl -X POST http://ANDROID_TV_IP:8765/close \
  -H 'Authorization: Bearer TOKEN'
```

Stage 4 adds pairing and request authentication. Use `Reset Pairing` on the TV app when testing a fresh token exchange.

The Android TV main screen displays the local endpoint address when available. Duplicate `/show` requests replace current playback, and `durationSeconds` should close either full-screen playback or the overlay fallback.

Stage 3 local discovery testing:

```sh
curl http://ANDROID_TV_IP:8765/status
```

Check the `discovery` object in the response. A healthy Android-side advertisement should report:

```json
{
  "running": true,
  "serviceType": "_ha-tv-pip._tcp.",
  "port": 8765
}
```

The Android TV main screen also reports whether discovery is advertising.

The Home Assistant integration declares a Zeroconf matcher for `_ha-tv-pip._tcp.local.`, includes discovery setup, starts pairing, and stores the returned token after the user enters the TV-visible code. Local Python tests cover discovery metadata parsing, config-flow helpers, and receiver client error handling.

Stage 7 Home Assistant stream type testing:

```yaml
action: ha_tv_pip.show_camera
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
  stream_type: auto
  snapshot_fallback: true
  snapshot_camera_entity: camera.front_door_sub
```

Use the Home Assistant device ID for `receiver_device_id` and a camera entity that exposes a TV-compatible HLS stream. `stream_type` defaults to `auto`, which prefers HLS and falls back to a snapshot command if Home Assistant cannot resolve a stream. Advanced calls can force `stream_type: hls` or `stream_type: snapshot`. `snapshot_fallback` is optional and enabled by default; it lets the receiver show a camera snapshot while the video stream loads. `snapshot_camera_entity` is optional and defaults to `camera_entity`, which is useful when a secondary camera entity provides a faster or lower-resolution still preview. Lower-resolution or H.264 camera streams are generally more reliable for TV popups than high-resolution main streams. The Android receiver enables Media3 decoder fallback and shows a clear unsupported-stream message, but it cannot replace transcoding for unsupported camera formats.

Stage 8 is complete in `0.26.0`. It includes receiver status, connected, test, close, diagnostics, Hide Launcher, and Open Launcher controls.

Phase 9 remote receiver testing:

```sh
curl http://ANDROID_TV_IP:8765/status
```

Check the `remote` object:

```json
{
  "status": "disabled"
}
```

After syncing remote config from Home Assistant, the Android TV app should show saved remote receiver details and the status should move through `connecting` to `connected`.

Remote mode uses Home Assistant's own WebSocket API and the existing receiver pairing token. It should not be described as a HA TV PiP cloud service.

Manual remote receiver URL/token entry remains available under the Android TV app's advanced manual setup control for troubleshooting. It is not the preferred setup path for normal users.

Receiver playback diagnostics:

```sh
curl http://ANDROID_TV_IP:8765/status
```

Check `playbackState`, `displayMode`, `url`, and `error` after triggering the service.

Stage 6 snapshot service testing:

```yaml
action: ha_tv_pip.show_snapshot
data:
  receiver_device_id: living_room_tv
  camera_entity: camera.front_door
  duration_seconds: 10
  enter_pip: true
```

Snapshot mode uses the Home Assistant camera proxy URL and the Android TV overlay renderer. It is intended for fast alerts and for cameras where live playback is unnecessary or unreliable.

Stage 6 is complete in `0.23.0`. It includes `ha_tv_pip.show_snapshot` plus optional entity-based snapshot previews for `ha_tv_pip.show_camera`.

Stage 7 is complete in `0.24.0`. It adds `stream_type: auto`, `stream_type: hls`, and `stream_type: snapshot` to `ha_tv_pip.show_camera`. Automatic mode prefers HLS, falls back to snapshot when stream resolution fails, and keeps the snapshot preview visible if receiver playback fails after an HLS URL is accepted.
