# Play Store Release Prep 📺

This document prepares HA TV PiP for a future Android TV / Google TV Play Store release. It does not implement Play Console deployment or submission yet.

## Current Release Position 🚦

HA TV PiP is still pre-release software. GitHub Releases remain the distribution target for now, while HACS custom-repository installation is prepared for the Home Assistant integration.

Stage 12 proved the beta release path through GitHub Releases and HACS custom-repository installs. Post-v1.0 release work now produces signed APK/AAB artifacts when signing secrets are configured, publishes a public privacy URL, and keeps listing metadata in source control.

The current external blocker is Google Play developer account verification. While that is pending, use these companion checklists to finish everything that can be prepared outside Play Console:

- `docs/play-console-submission.md` - app creation, reviewer notes, testing track, and manual Console steps.
- `docs/play-store-data-safety.md` - working answer sheet for the Play data-safety form.
- `docs/play-store-assets.md` - screenshots, graphics, and privacy-safe capture guidance.
- `docs/release-qa.md` - release and device smoke-test checklist.

The Android app package name is:

```txt
com.hatvpip.receiver
```

The Play Store release track should start as internal testing, then closed testing, before any public production release.

Fastlane-compatible listing metadata drafts live in:

```txt
android-tv-app/fastlane/metadata/
```

These files are source-controlled preparation only. They are not wired to Play Console upload or deployment yet.

## Store Listing Draft 📝

### App Name

```txt
HA TV PiP Receiver
```

### Short Description

```txt
Show Home Assistant camera alerts on Android TV in PiP or overlay mode.
```

### Full Description

```txt
HA TV PiP Receiver is a local-first Android TV companion app for Home Assistant.

Use Home Assistant automations to show camera streams, snapshots, and visual alerts on Android TV and Google TV devices. The receiver supports Android Picture-in-Picture where available and uses a local overlay fallback on devices that do not expose native PiP to third-party TV apps.

Current features:
- Home Assistant discovery and pairing
- TV-visible pairing code
- Authenticated local receiver control
- Camera stream popups
- Snapshot popups
- Snapshot fallback while video loads
- Receiver status and diagnostics
- Optional launcher hiding with Home Assistant recovery controls
- Optional remote receiver mode using your own Home Assistant external URL

HA TV PiP is not a cloud relay service. Remote receiver mode connects back to your own Home Assistant instance. The project does not collect analytics, telemetry, or usage data.
```

### Tags And Positioning

- Home Assistant
- Android TV
- Google TV
- Smart home
- Security camera
- Picture-in-Picture
- Local-first

## Privacy Wording 🔒

Use this wording as the Play Store privacy summary:

```txt
HA TV PiP Receiver does not collect, sell, or share personal data with the project maintainers. The app does not include analytics, advertising SDKs, telemetry SDKs, or a HA TV PiP cloud relay.

The app uses network access to communicate with your Home Assistant instance, load camera streams or snapshots you request, advertise and run a local receiver endpoint on your LAN, and optionally maintain an outbound connection to your own Home Assistant external URL for remote receiver mode.

Pairing tokens and receiver settings are stored locally on the Android TV device and in your Home Assistant instance. Camera stream and snapshot URLs are only used to display requested notifications on paired receivers.
```

Reference policy:

```txt
PRIVACY.md
```

Public Play Console URL after website deployment:

```txt
https://manix84.github.io/ha-tv-pip/privacy/
```

The deployed page is generated from `website/public/privacy/index.html` and should stay aligned with root `PRIVACY.md`.

## Data Safety Prep 🛡️

Expected Play Console answers for the current implementation:

- Data collected by developer: No.
- Data shared with third parties by developer: No.
- Analytics SDKs: No.
- Advertising SDKs: No.
- Account creation: No.
- User-generated content: No.
- Location data: No.
- Contacts/calendar/messages/photos/files: No.
- Device identifiers collected by developer: No.
- App activity collected by developer: No.
- Crash logs sent to developer automatically: No.

Network and local storage behavior:

- The app communicates with Home Assistant and configured media URLs.
- The app stores local pairing and remote receiver settings on the Android TV device.
- The app can write local Android logs for debugging.
- Logs are not uploaded by the app.

Review again before enabling any hosted relay, external analytics, crash reporting SDK, or third-party telemetry.

## Permissions Explanation 🔐

Current Android permissions and Play Store-facing explanation:

- `INTERNET`: required to communicate with Home Assistant and load camera streams or snapshots.
- `RECEIVE_BOOT_COMPLETED`: allows the receiver service to become available again after the TV restarts.
- `FOREGROUND_SERVICE` / `FOREGROUND_SERVICE_DATA_SYNC`: keeps the local receiver service available while the app listens for paired Home Assistant commands.
- `SYSTEM_ALERT_WINDOW`: enables the overlay fallback on Google TV devices that do not expose native Picture-in-Picture to third-party TV apps.

The overlay permission is user-granted from Android settings. The app should clearly explain that this is used only for local floating camera popups.

## Screenshots And Graphics Checklist 🖼️

Capture real Android TV / Google TV screenshots for:

- Receiver dashboard idle state.
- Pairing popup with code visible. Use a disposable test code only.
- PiP controls section.
- Remote receiver section showing configured state without exposing tokens.
- Overlay/PiP camera popup using a non-sensitive test stream.
- Snapshot popup.
- Home Assistant device page showing PiP controls and launcher controls.
- Website hero or project overview for supporting marketing material.

Graphic assets to prepare:

- TV banner image.
- App icon.
- Feature graphic.
- At least 2 Android TV screenshots.
- Optional tablet/phone screenshots only if Play Console requests them for listing completeness.

Personal developer avatar/header graphics can be used for the Play developer profile or account presence if needed, but the app listing should remain product-led and use HA TV PiP-specific app graphics.

Safety rules:

- Do not show real security cameras, real home interiors, real addresses, access tokens, pairing tokens, LAN IPs, or Nabu Casa URLs.
- Use public demo streams, mock snapshots, or staged test cameras.
- Use the current project icon and banner until a final brand pass replaces them.

## Signing Guidance ✍️

Release builds can now be signed when a complete signing configuration is provided. Before Play Store upload:

1. Decide whether to use Play App Signing.
2. Generate a production upload key and keep it outside the repository.
3. Add local signing configuration through Gradle properties or CI secrets.
4. Build an Android App Bundle (`.aab`) for Play Store upload.
5. Keep debug, release, upload-key, and Play signing responsibilities documented separately.

Local signing values can be provided through Gradle properties or environment variables:

```txt
HA_TV_PIP_RELEASE_STORE_FILE=/absolute/path/to/release.keystore
HA_TV_PIP_RELEASE_STORE_PASSWORD=...
HA_TV_PIP_RELEASE_KEY_ALIAS=...
HA_TV_PIP_RELEASE_KEY_PASSWORD=...
```

GitHub Actions release signing uses repository secrets:

```txt
ANDROID_RELEASE_KEYSTORE_BASE64
ANDROID_RELEASE_STORE_PASSWORD
ANDROID_RELEASE_KEY_ALIAS
ANDROID_RELEASE_KEY_PASSWORD
```

If those secrets are absent, the release workflow falls back to the unsigned release APK so beta release validation can continue.
If only some signing secrets are configured, the workflow fails before building so it cannot accidentally publish an unsigned artifact that looked signed. When all signing secrets are configured, the workflow verifies the APK with Android SDK `apksigner` before upload.

Local bundle build:

```sh
npm run android:bundle:release
```

Current output:

```txt
android-tv-app/app/build/outputs/bundle/release/app-release.aab
```

GitHub Releases also attach a Play Console-ready bundle named:

```txt
ha-tv-pip-android-release-vX.Y.Z.aab
```

The AAB is for Play Console upload only. Users should continue to sideload `ha-tv-pip-android-release-vX.Y.Z.apk` until Play Store distribution is active.

Do not commit keystores, passwords, generated signing reports, or Play Console credentials.

The current automation builds the release APK and App Bundle, and signs them when Android release signing secrets are configured. Play Store upload remains a future task.

## Release Notes Guidance 📦

Play Store release notes should be short and user-facing. Avoid internal stage names unless helpful.

Initial internal testing notes:

```txt
Initial Android TV receiver test release.

- Pair with Home Assistant using a TV-visible code.
- Show camera streams and snapshots from Home Assistant.
- Use native PiP where available or the overlay fallback on supported devices.
- Manage receiver status, launcher visibility, and remote receiver setup.
```

Production release notes should include:

- New user-visible features.
- Any setup or permission changes.
- Known limitations, especially camera codec compatibility.
- Whether this is local-only, remote-capable, or still pre-release.

## Pre-Submission Checklist ✅

- Full `npm run check` passes.
- `docs/play-console-submission.md` is reviewed for current Play Console fields.
- `docs/play-store-data-safety.md` still matches the actual app behavior.
- `docs/play-store-assets.md` has enough privacy-safe screenshot coverage.
- `docs/release-qa.md` has been run for the candidate release.
- Website build passes.
- Home Assistant integration package builds.
- Android debug APK builds.
- Android release APK builds.
- Android release APK is signed when signing secrets are configured.
- Android App Bundle build exists.
- GitHub Release includes `ha-tv-pip-android-release-vX.Y.Z.aab`.
- Release artifact version matches root `package.json`.
- `PRIVACY.md` matches Play Console privacy answers.
- Store listing screenshots contain no sensitive user data.
- `android-tv-app/fastlane/metadata/` matches the current Play Store listing draft.
- Overlay permission explanation is visible in docs and app UX.
- HACS release zip remains available for the integration.

## Not Yet Implemented 🚧

- Play Store deployment.
- Play Console metadata upload.
- Store screenshot generation automation.
- Public production release approval.
