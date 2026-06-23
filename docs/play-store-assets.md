# Play Store Assets Checklist 🖼️

This checklist tracks Play Store listing assets, promotional graphics, and safe screenshot capture for HA TV PiP.

## Product Assets ✅

Use product-focused HA TV PiP assets for the public app listing:

- App icon: current HA TV PiP icon assets in the Android project and root brand folders.
- TV banner: current Android TV banner assets in the Android project.
- Feature graphic: prepare from HA TV PiP visuals, not personal profile graphics.
- Screenshots: capture from the Android TV receiver and Home Assistant integration using non-sensitive data.

Personal profile assets, such as the developer avatar or account header banner, are suitable for the developer profile or account identity areas if Play Console asks for them. They should not replace the app icon, feature graphic, TV banner, or product screenshots.

Available developer profile/account assets:

- `docs/assets/avatar.png` - 512 x 512 developer avatar.
- `docs/assets/header.png` - 4096 x 2304 developer/account header banner.

Check Play Console's current file-size and dimension limits during upload. If the banner is too large for the Console limit, resize/compress a derived copy and keep the original source asset unchanged.

## Required Screenshot Set 📸

Capture at least these Android TV screenshots before the first public Play listing:

- Receiver dashboard idle state.
- Receiver dashboard showing connected state and version alignment.
- Pairing popup with a disposable test code.
- PiP controls and launcher controls visible.
- Remote receiver section configured, with token and external URL hidden or mocked.
- Camera popup using a public demo stream or staged non-private test feed.
- Snapshot popup using a staged non-private image.
- Unsupported stream / fallback state using neutral test content.

Optional supporting screenshots:

- Home Assistant device page showing PiP controls.
- Home Assistant service UI for `ha_tv_pip.show_camera`.
- Website landing page hero.

## Privacy Rules 🔐

Do not show:

- Real security camera feeds.
- Real home interiors.
- LAN IP addresses.
- Nabu Casa URLs.
- Pairing codes that are still valid.
- Bearer tokens.
- Home Assistant device IDs.
- Personal profile rows from the TV launcher.
- Media titles or recommendations from personal streaming accounts.

Use public demo streams, generated mock imagery, staged test entities, or censored captures.

## Capture Guidance 🎮

Preferred capture targets:

- Android TV emulator for clean dashboard and setup screenshots.
- Physical Chromecast / Google TV for real overlay and PiP screenshots.
- Home Assistant test instance or redacted production instance for integration screenshots.

Before committing screenshots:

1. Zoom in and inspect every visible URL, token, entity, and ID.
2. Redact or recapture if any private value is visible.
3. Save promotion-ready screenshots under `docs/assets/screenshots/`.
4. Prefer PNG for UI captures.
5. Keep raw, sensitive screenshots outside the repository.

## Current Repository Assets 📦

- `docs/assets/screenshots/android-tv-dashboard.png` exists as a sanitized Android TV dashboard capture.
- `docs/assets/screenshots/android-tv-camera-popup.png` and `android-tv-camera-notification.png` show cropped popup detail captures.
- `docs/assets/screenshots/android-tv-homepage-camera-popup.png` and `android-tv-homepage-camera-notification.png` show full Google TV launcher captures with the profile avatar replaced.
- `docs/assets/screenshots/android-tv-homepage-camera-popup.jpg` and `android-tv-homepage-camera-notification.jpg` are web-optimized README copies; use the PNGs if Play Console accepts the larger source captures cleanly.
- `brand/`, `icon.png`, and `logo.png` support HACS / repository presentation.
- Android launcher and TV banner assets live in the Android app resources.
- Website imagery lives under `website/src/assets/`.
- Play listing text lives under `android-tv-app/fastlane/metadata/`.

## Before Public Store Submission ✅

- Capture additional setup and Home Assistant screenshots.
- Confirm the feature graphic matches the HA TV PiP brand rather than a generic smart-home graphic.
- Confirm screenshots still match the current app UI.
- Confirm no screenshot exposes private camera, network, or account data.
