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

New user-facing strings should be designed with translation in mind. The main Tier 1 translation implementation pass happened during Phase 10 distribution polish.

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
npm run website:a11y
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
npm run website:a11y
npm run website:test
npm run website:typecheck
npm run android:build:dry-run
npm run ha:build:dry-run
npm run website:build:dry-run
```

Quality tooling by area:

- Android TV app: Android Gradle Plugin lint, JVM unit tests, and Kotlin debug compilation.
- Home Assistant integration: Ruff, pytest, and MyPy against the custom integration package.
- Website: ESLint for React/TypeScript, Vitest, static accessibility assertions, and `tsc --noEmit` for type checking.

Dry-run builds by area:

- Android TV app: assembles the debug APK.
- Home Assistant integration: packages the custom integration zip from `custom_components/ha_tv_pip/`.
- Website: runs the Vite production build.

GitHub Actions runs project-specific quality workflows for the Android TV app, Home Assistant integration, and website. Each workflow still exposes separate jobs, such as `website: lint`, `website: accessibility`, `website: test`, `website: typecheck`, and `website: build dry-run`. The Website Deploy workflow only builds/deploys the site, and the Release workflow only packages release assets.

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
custom_components/ha_tv_pip/
```

Example:

```txt
0.2.4 -> 0.2.5
```

### MINOR Bumps 🚦

MINOR bumps are conservative. The automatic hook defaults normal runtime work to PATCH, even when the change touches API, service, discovery, pairing, or compatibility code. This keeps frequent project releases small and predictable.

Use a MINOR bump when a change is meaningfully user-visible, adds a larger capability, or changes an integration/receiver contract in a way that downstream users should notice in the release number.

Automatic MINOR bumps happen when staged changes look like larger product work:

- An explicit MINOR marker is present in the staged diff.
- Runtime changes span both the Android TV app and the Home Assistant integration.
- Runtime changes are unusually large, currently 250 changed lines or more.

Explicit markers:

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

You can also force a MINOR bump with `VERSION_BUMP=minor`.

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

Release builds are signed when a complete signing configuration is provided through Gradle properties or environment variables:

```txt
HA_TV_PIP_RELEASE_STORE_FILE=/absolute/path/to/release.keystore
HA_TV_PIP_RELEASE_STORE_PASSWORD=...
HA_TV_PIP_RELEASE_KEY_ALIAS=...
HA_TV_PIP_RELEASE_KEY_PASSWORD=...
```

Without those values, local release builds remain unsigned and continue to produce `app-release-unsigned.apk` for beta validation. Do not commit keystores, passwords, signing reports, or Play Console credentials.

The GitHub release workflow can sign the release APK when these repository secrets are configured:

```txt
ANDROID_RELEASE_KEYSTORE_BASE64
ANDROID_RELEASE_STORE_PASSWORD
ANDROID_RELEASE_KEY_ALIAS
ANDROID_RELEASE_KEY_PASSWORD
```

`ANDROID_RELEASE_KEYSTORE_BASE64` should be the base64-encoded keystore file. The workflow decodes it into the runner temp directory and exposes it to Gradle as `HA_TV_PIP_RELEASE_STORE_FILE`.

Signing secrets are all-or-nothing. If only part of the secret set is configured, the release workflow fails before building the release APK. When all signing secrets are present, the workflow verifies the signed APK with Android SDK `apksigner` before uploading the release asset.

Play Store deployment is intentionally out of scope. Play Store listing, privacy, screenshot, signing, and release-note prep is tracked in `docs/play-store.md`.

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

The versioned zip preserves the Home Assistant manual install path:

```txt
custom_components/ha_tv_pip/
```

The stable HACS zip contains the integration files at archive root:

```txt
manifest.json
__init__.py
brand/
translations/
...
```

The versioned zip is the human-readable/manual-install release asset. The stable `ha-tv-pip-integration.zip` file is the HACS release asset referenced by root `hacs.json`. HACS extracts `zip_release` assets directly into `config/custom_components/ha_tv_pip/`, so the stable HACS zip must not contain a leading `custom_components/ha_tv_pip/` folder.

## GitHub Release Assets

When code is pushed or merged into `main`, `.github/workflows/release.yml`:

1. Runs `Setup release metadata 🧭` to read the release version from root `package.json` and run the version consistency check.
2. Runs `Android APK Debug 🤖` to build and stage the debug APK.
3. Runs `Android APK Release 🤖` to build and stage the release APK.
4. Runs `HA Integration Release 🏠` to package the Home Assistant integration zips.
5. Runs `Release Asset Check 🔎` to validate APK names, APK archive shape, integration zip names, HACS zip layout, manual zip layout, icon presence, ignored paths, and manifest version consistency.
6. Runs `Publish Release 🚀` to generate release notes from `WHATSNEW.md`, create draft GitHub Release `vX.Y.Z` with the Android APKs, versioned integration zip, and stable HACS integration zip already attached, then publishes it.
7. Runs `Cleanup 🧹` as a final visible workflow stage.

The `Android APK Release 🤖` job signs and verifies the release APK when all Android signing secrets are available. If signing secrets are absent, it uploads the unsigned release APK under the same release asset name so beta release validation can continue. Partial signing configuration fails the job.

Release notes are generated by `scripts/generate-release-notes.mjs`. The workflow finds the latest existing published GitHub Release and includes every matching `WHATSNEW.md` section newer than that version, up to the current root `package.json` version. If there is no previous published release, it uses the current version's `WHATSNEW.md` section.

Published GitHub Releases are treated as immutable. The workflow will not replace assets on an existing published release; it exits cleanly when the release for the current version already exists. Bump the root `package.json` version before producing another release. If an older failed workflow already created a published release without assets, delete that failed release manually or move forward with the next version.

For version `1.2.3`, expected release assets are:

```txt
ha-tv-pip-android-debug-v1.2.3.apk
ha-tv-pip-android-release-v1.2.3.apk
ha-tv-pip-integration-v1.2.3.zip
ha-tv-pip-integration.zip
```

The same release asset validation can be run locally after building the APKs and packaging the integration:

```sh
npm run package:release:check
```

## HACS Distribution

HACS expects custom integration repositories to provide a root `hacs.json` and installable integration content under `custom_components/<domain>/`. HA TV PiP keeps the integration source at `custom_components/ha_tv_pip/` so the monorepo remains directly HACS-compliant without duplicated source folders.

HACS renders the repository-root `README.md` for the store page, so the root README starts with user install guidance: Android APK first, Home Assistant integration second, and pairing third. Development and monorepo details are kept lower in the README. Integration-specific operational notes still live in `custom_components/ha_tv_pip/README.md`.

HACS also expects repository brand assets. The repo keeps presentation assets in root `brand/` for HACS, root `icon.png` / `logo.png` compatibility aliases for older/simple presentation paths, and installed integration assets in `custom_components/ha_tv_pip/brand/` for Home Assistant.

The repo therefore uses root `hacs.json` with:

```json
{
  "name": "HA TV PiP",
  "zip_release": true,
  "filename": "ha-tv-pip-integration.zip",
  "hide_default_branch": true
}
```

The release workflow attaches that stable zip while creating the draft GitHub Release from `main`. Its internal path starts at the integration files:

```txt
manifest.json
__init__.py
brand/
translations/
```

For custom-repository installs, users should add `https://github.com/manix84/ha-tv-pip` in HACS as category `Integration`.

Use `v1.27.9` or newer as the practical HACS beta baseline. Earlier HACS beta builds had a frontend serialization failure in the integration options flow because raw `vol.Any(...)` dropdown schemas cannot be converted by Home Assistant's config-flow API. The fixed options flow uses Home Assistant selector dropdowns for stream strategy and popup position.

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
npm run package:release:check
npm run website:build
```

Verify release packaging expectations:

- Android debug APK asset: `ha-tv-pip-android-debug-vX.Y.Z.apk`.
- Android release APK asset: `ha-tv-pip-android-release-vX.Y.Z.apk`.
- Versioned integration zip: `ha-tv-pip-integration-vX.Y.Z.zip`.
- Stable HACS integration zip: `ha-tv-pip-integration.zip`.
- Versioned integration zip internal path: `custom_components/ha_tv_pip/`.
- Stable HACS zip internal path: integration files at archive root.
- Root `package.json`, Android `versionName`, HA `manifest.json`, and project `package.json` files all match.
- HACS install/update can open the receiver Configuration screen without a `500` error.
- Receiver device exposes Status, Receiver Version, Receiver Compatibility, Last Command Result, Last Camera Compatibility, Camera Restreaming Recommended, and Last Camera Result entities.

Documentation work in Stage 12 included:

- Root README install flow.
- Android TV app install and sideload guidance.
- HACS custom-repository install guidance.
- Manual custom integration fallback guidance.
- Website current status and Stage 11 notification examples.
- Example automations for text-only notifications, camera with footer, snapshot with footer, and resize-only media popups.
- Release notes for the beta candidate.

Stage 12 finished with GitHub Release `v0.48.0` from `main` after local checks, builds, packaging, website build, and docs were clean.

## Current Beta Install/Update Validation

The `1.27.0` beta install/update path was locally validated with:

```sh
npm run version:check
npm run android:assemble:debug
npm run android:assemble:release
npm run package:integration
```

Validated outputs:

- `dist/ha-tv-pip-android-debug-v1.27.0.apk`
- `dist/ha-tv-pip-android-release-v1.27.0.apk`
- `dist/ha-tv-pip-integration-v1.27.0.zip`
- `dist/ha-tv-pip-integration.zip`

The versioned integration zip was checked to confirm it contains `custom_components/ha_tv_pip/` at the archive root. The stable HACS zip was checked to confirm it contains the integration files directly at archive root. Neither zip should include unrelated monorepo paths such as `ha-integration/`, `android-tv-app/`, `docs/`, `dist/`, `.git/`, or `node_modules/`.

Recommended beta update order:

1. Update the Home Assistant integration through HACS.
2. Restart Home Assistant.
3. Install the matching Android receiver APK on each TV.
4. Confirm receiver status and compatibility sensors show matching receiver/integration versions where available.

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
custom_components/ha_tv_pip/
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
- Website: ESLint, TypeScript type checking, Vitest, and static accessibility assertions for key interactive and media surfaces.

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
Post-v1.0 compatibility polish
Camera compatibility, receiver diagnostics, and restreaming groundwork
```

The active Post-v1.0 track focuses on practical camera compatibility, per-camera defaults, receiver capability diagnostics, and visible restreaming guidance. Stage 12 remains completed release hardening history, not the current active phase.

The Android TV dashboard keeps onboarding, pairing, troubleshooting, receiver controls, and diagnostics in one TV-first surface for now. Separate screens are deferred until the setup flow becomes large enough to justify deeper navigation.

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
The `/status` response keeps legacy top-level playback fields and also includes a nested `playback` object with `state`, `status`, `isPlaying`, `displayMode`, `title`, `url`, `previewUrl`, `streamType`, `error`, and `updatedAtMillis` for debugging stream compatibility without showing fallback implementation details in the TV popup.
The `/status` response also includes a `service` diagnostics object with `running`, `foreground`, `startCount`, `lastStartReason`, `lastStartedAtMillis`, `lastDestroyedAtMillis`, `lastBootReceiverAction`, and `lastBootReceiverAtMillis`. Use these fields to confirm whether Android delivered boot/package-replaced events and whether the local foreground receiver service restarted after TV reboot, app update, or process restart.
The receiver's MJPEG parser uses connection/read timeouts and an 8 MiB per-frame limit so broken camera proxy streams fail cleanly instead of growing memory use indefinitely.

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

The Home Assistant integration declares a Zeroconf matcher for `_ha-tv-pip._tcp.local.`, includes discovery setup, starts pairing, and stores the returned token after the user enters the TV-visible code. When an existing receiver is rediscovered, the config flow refreshes host, port, version, pairing, and API metadata by stable receiver id so DHCP address changes repair automatically. Local Python tests cover discovery metadata parsing, config-flow helpers, discovery repair metadata, and receiver client error handling.

Stage 7 Home Assistant stream type testing:

```yaml
action: ha_tv_pip.show_camera
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  duration_seconds: 30
  enter_pip: true
  stream_type: auto
  stream_camera_entity: camera.front_door_sub
  snapshot_fallback: true
  snapshot_camera_entity: camera.front_door_sub
```

Use the standard Home Assistant `target.device_id` selector for the HA TV PiP receiver and a camera entity that exposes a TV-compatible stream. The target selector is limited to HA TV PiP devices. Each receiver can define action defaults in the integration options for preferred stream strategy, duration, popup position, snapshot fallback, width, and height. Service-call data always wins over receiver defaults; omitted values use the receiver defaults first, then the built-in service defaults.

Per-camera defaults are stored through `ha_tv_pip.set_camera_defaults` and removed through `ha_tv_pip.clear_camera_defaults`. They apply before receiver-level defaults. Use them for cameras that need a specific stream strategy, substream entity, snapshot entity, popup size, duration, or position without repeating those values in every automation.

Use `ha_tv_pip.clear_all_camera_defaults` to remove every saved per-camera default for one receiver. The action resolves the receiver from `target.device_id`, leaves receiver-level defaults intact, and returns the cleared camera count plus entity IDs.

`ha_tv_pip.test_camera_stream` checks HLS, MJPEG, and snapshot URL availability for a camera/receiver pair. The test result is stored in config entry diagnostics without active stream URLs, so users can share compatibility data without exposing camera endpoints.

`ha_tv_pip.calibrate_camera` wraps the compatibility test in a friendlier workflow. It returns a `summary` object with compatibility, recommended stream type, recommendation reason, whether defaults were saved, and a next-step hint. The response also includes `action_plan`, which gives support tools and dashboards a stable primary action key, readable label, suggested HA TV PiP service, safe payload, optional fields to try, and short notes. Use `save: true` to store the recommended stream strategy plus any explicit calibration fields as per-camera defaults.

Calibration and compatibility responses also include `restreaming_recommended`, `restreaming_reason`, `restreaming_next_step`, `restreaming_options`, and `restreaming_provider`. These fields are populated when HLS and MJPEG are unavailable, or when the receiver/camera path is snapshot-only. Treat them as a signal to try a different camera entity, a lower-resolution profile, a TV-safe H.264/HLS or MJPEG substream, a manual `restream_url`, or, in the future, automatic go2rtc, WebRTC, or transcoding support.

Use `ha_tv_pip.suggest_restream_source` to generate advisory manual restream setup values for a selected camera and receiver. It returns candidate stream names, go2rtc-style HLS/MJPEG URL patterns, provider help, the effective `restream_base_url`, and a safe follow-up `save_restream_source` payload. It does not create provider streams.

Use `ha_tv_pip.test_restream_source` to validate a candidate manual restream URL before saving it. It infers HLS or MJPEG from the URL, checks receiver stream capability metadata, optionally checks reachability from Home Assistant, and returns a `save_action` payload when the URL should be saved as a per-camera default.

Camera compatibility and calibration responses include `restream_source_suggestion` automatically when `restreaming_recommended` is true. This keeps the manual restream workflow discoverable from the first failing or snapshot-only test result.

See [camera compatibility](camera-compatibility.md) for the current TV-safe stream workflow, calibration loop, snapshot fallback guidance, and planned restreaming provider model.

See [troubleshooting](troubleshooting.md) for the public beta support path, including discovery, pairing, launcher recovery, remote receiver checks, stream compatibility checks, and the diagnostics expected in bug reports.

Stored per-camera defaults are exposed in config entry diagnostics. A recommended troubleshooting loop is: run `ha_tv_pip.calibrate_camera` with `save: false`, inspect `recommended_defaults`, run again with `save: true` when the recommendation looks right, then use `ha_tv_pip.show_camera` with only the receiver target and `camera_entity`.

The compatibility test includes `recommended_stream_type` and `recommendation_reason`. `auto` is recommended when HLS is available and the receiver can carry an MJPEG playable fallback. `mjpeg_first` is recommended when HLS and MJPEG are available but playable fallback is not, because it reduces receiver decoder risk while still allowing HLS fallback. HLS, MJPEG, or snapshot are recommended when only those paths are available.

`restreaming_reason` is intentionally separate from `recommended_stream_type`. A snapshot recommendation can still be valid for fast alerts, while `snapshot_only_live_stream_restreaming_recommended` explains that live video likely needs another source. `no_supported_stream_paths_restreaming_recommended` means Home Assistant could not resolve a supported HLS, MJPEG, or snapshot path for the selected camera/receiver pair. `restreaming_next_step` gives the broad next action, `restreaming_options` lists stable option keys that can be translated or rendered by future UI helpers, and `restreaming_provider` exposes current workaround paths plus planned provider families.

The response also includes `recommended_defaults`, which previews the exact per-camera defaults that would be saved. This lets users inspect the recommendation before setting `save_recommendation: true`. Direct restream URLs are not duplicated into `action_plan`; use `recommended_defaults` when the user needs to inspect or save an explicit restream URL.

Set `save_recommendation: true` on `ha_tv_pip.test_camera_stream` to write the recommended stream strategy into per-camera defaults. Explicit test fields are saved alongside the recommendation, so a calibration action can set `mjpeg_first`, snapshot fallback, dimensions, position, duration, alternate stream/snapshot entities, and manual restream URL/provider metadata in one pass. If the test cannot recommend a compatible stream type, no defaults are written.

The latest compatibility test is also exposed through the receiver's `Last Camera Compatibility` sensor. The sensor state is the recommended stream type and the attributes include the tested camera, recommendation reason, action plan, stream availability results, source classification, and timestamp.

Saved per-camera defaults are exposed through the receiver's `Saved Camera Defaults` sensor. The sensor state is the saved camera count, and attributes list saved cameras plus restream-enabled cameras without exposing raw restream URLs.

Only the receiver Status sensor is intended as the primary day-to-day state. Detailed receiver, compatibility, command-result, connectivity, restreaming, and saved-defaults entities are diagnostic entities so Home Assistant can keep the device page focused while retaining support data.

The receiver also exposes a `Camera Restreaming Recommended` binary sensor. It turns on when the latest compatibility result includes `restreaming_recommended: true`, with attributes for the camera entity, recommended stream type, recommendation reason, restreaming reason, next step, suggested options, current workaround paths, planned provider families, documentation URL, and timestamp.

The `Restreaming Provider Status` sensor and diagnostics expose the same provider metadata. Automatic provider support is currently `planned`; current recommended paths are `use_stream_camera_entity`, `use_mjpeg_first`, `use_snapshot_fallback`, `use_camera_substream`, `use_restream_url`, and `save_per_camera_defaults`.

Real camera and snapshot actions store a redacted last camera result under the receiver. The `Last Camera Result` sensor and config entry diagnostics expose status, stage, requested stream type, final stream type, stream source classification, transport, fallback flags, size, and failure reason without storing stream URLs. The `Last Command Result` sensor is broader and records the latest receiver command type, accepted/failed status, transport, final stream type where applicable, failure stage, reason, and update time for camera, snapshot, and notification actions.

Receiver/integration compatibility is also calculated from `/status` API and capability metadata. Current receivers should report `compatible`; older receivers without capability metadata are treated as `legacy` best-effort; receivers missing optional presentation, fallback, launcher, or remote settings support report `degraded`; receivers missing required API or display stream support report `incompatible`. These fields are exposed on the status sensor attributes and in diagnostics.

Receiver service health is exposed on the status sensor attributes and diagnostics. Check `service_running`, `service_foreground`, `service_start_count`, `service_last_start_reason`, `last_boot_receiver_action`, and the related timestamp fields when debugging reboot, app-update, or background-service startup issues.

Remote receiver health is exposed on the status sensor and Remote Connected binary sensor attributes. Check `remote_connection_attempt_count`, `remote_successful_connection_count`, `remote_message_count`, `remote_last_error`, `remote_last_disconnect_reason`, and the related timestamp fields when debugging external-TV transport. The actual configured external Home Assistant URL remains in redacted diagnostics only; entity attributes expose whether a remote URL is configured, not the URL itself.

The receiver options flow intentionally starts with a compact everyday defaults screen. Advanced popup position, width, height, and remote URL/token fields live behind the Show advanced settings path. Saving the compact screen preserves existing advanced values so routine default changes do not clear remote receiver setup.

When a receiver lacks media text footer support, Home Assistant drops optional title/message footer fields from camera and snapshot commands instead of failing the whole action. This keeps older receivers useful while still surfacing the missing feature in diagnostics.

`stream_type` falls back to the receiver's preferred stream strategy, or `auto` when no receiver default is configured. Automatic mode prefers HLS when the receiver supports playable fallback and sends an optional MJPEG `fallbackUrl` when Home Assistant can create one, so the Android overlay can switch to MJPEG if the accepted HLS URL later fails decoder playback. If the receiver does not support playable fallback, automatic mode prefers MJPEG first when available, then falls back through HLS and snapshot. Advanced calls can force `stream_type: hls`, force `stream_type: mjpeg`, prefer MJPEG with fallback using `stream_type: mjpeg_first`, or force `stream_type: snapshot`. `stream_type: mjpeg` uses Home Assistant's camera proxy stream endpoint and the Android overlay renderer. `stream_type: mjpeg_first` uses MJPEG first, then HLS, then snapshot.

`stream_camera_entity` is optional and defaults to `camera_entity`; use it when a separate lower-resolution, H.264, or MJPEG entity is more reliable for live playback on Android TV. `restream_url` is optional and takes precedence over Home Assistant camera stream resolution for live video; use it for a known TV-safe HLS or MJPEG URL from go2rtc or another local restreaming tool. `snapshot_fallback` is optional and uses the receiver default when configured, otherwise it is enabled by default. It lets the receiver show a camera snapshot while the video stream loads. `snapshot_camera_entity` is optional and defaults to `camera_entity`, which is useful when a secondary camera entity provides a faster or lower-resolution still preview. Lower-resolution, H.264, or MJPEG camera streams are generally more reliable for TV popups than high-resolution main streams. The Android receiver enables Media3 decoder fallback and shows a clear unsupported-stream message, but it cannot replace transcoding for unsupported camera formats.

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
target:
  device_id: living_room_tv
data:
  camera_entity: camera.front_door
  duration_seconds: 10
  enter_pip: true
```

Snapshot mode uses the Home Assistant camera proxy URL and the Android TV overlay renderer. It is intended for fast alerts and for cameras where live playback is unnecessary or unreliable.

Stage 6 is complete in `0.23.0`. It includes `ha_tv_pip.show_snapshot` plus optional entity-based snapshot previews for `ha_tv_pip.show_camera`.

Stage 7 is complete in `0.24.0`. It adds `stream_type: auto`, `stream_type: hls`, `stream_type: mjpeg`, `stream_type: mjpeg_first`, and `stream_type: snapshot` to `ha_tv_pip.show_camera`. Automatic mode prefers HLS when the receiver can carry playable fallback, prefers MJPEG first when the receiver cannot carry playable fallback, falls back to snapshot when stream URL resolution still fails, and keeps the snapshot preview visible if receiver playback fails after a video URL is accepted. `mjpeg_first` supports cameras where MJPEG is usually the better receiver path but HLS should still remain available as fallback.
