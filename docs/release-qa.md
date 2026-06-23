# Release QA Checklist ✅

Use this checklist before a GitHub beta release, HACS update, or Play Console test upload.

## Automated Checks 🤖

Run from the repository root:

```sh
npm run check
npm run website:build
npm run package:integration
npm run android:assemble:debug
npm run android:assemble:release
npm run android:bundle:release
npm run package:release:check
```

If Android SDK tools are not on the shell path, prefix commands with:

```sh
PATH="/usr/local/bin:$HOME/Library/Android/sdk/platform-tools:$PATH"
```

## GitHub Release Asset Checks 📦

For version `X.Y.Z`, the release should contain:

- `ha-tv-pip-android-debug-vX.Y.Z.apk`
- `ha-tv-pip-android-release-vX.Y.Z.apk`
- `ha-tv-pip-android-release-vX.Y.Z.aab`
- `ha-tv-pip-integration-vX.Y.Z.zip`
- `ha-tv-pip-integration.zip`

The stable `ha-tv-pip-integration.zip` file is the HACS `zip_release` asset. The AAB is for Play Console upload only.

## Android Receiver Smoke Test 📺

On a physical Android TV / Google TV device:

- Install the latest release or debug APK.
- Open the receiver dashboard.
- Confirm the app version matches the release.
- Confirm local receiver service is running.
- Confirm remote receiver status is either configured or intentionally disabled.
- Confirm focused buttons are visible and D-pad navigation works.
- Confirm `Play Test Video` works.
- Confirm `Test PiP` works.
- Confirm `Close PiP` works.
- Confirm launcher hide/open controls still work if enabled.
- Confirm reset/clear danger actions show warnings before running.

## Home Assistant Smoke Test 🏠

After updating through HACS or copying the integration:

- Restart Home Assistant.
- Confirm the installed integration version matches the Android app version.
- Confirm discovery finds the receiver by stable receiver identity.
- Confirm pairing works.
- Confirm the receiver Status sensor is available.
- Confirm Receiver Compatibility is compatible.
- Confirm no version mismatch repair is active when versions match.
- Confirm `Refresh Status`, `Test PiP`, and `Close PiP` work.
- Confirm `Prefer Remote Transport` defaults off.
- Confirm local-first transport works on LAN.
- Confirm remote-preferred transport works when remote receiver mode is configured.

## Camera And Notification Smoke Test 🎬

Run at least one safe test for each path:

- HLS camera or public HLS test stream.
- MJPEG camera or MJPEG test stream.
- Snapshot popup.
- Snapshot fallback before video.
- Notification-only popup.
- Media plus title/message popup.
- Unsupported stream fallback messaging.
- Per-camera saved defaults.
- Manual restream URL defaults if available.

Use non-sensitive cameras, public test streams, or staged test content.

## Diagnostics And Privacy 🔐

- Download config-entry diagnostics.
- Confirm diagnostics contain useful receiver status.
- Confirm diagnostics do not expose bearer tokens.
- Confirm camera URLs are redacted where expected.
- Confirm screenshots and logs do not expose private URLs, IPs, tokens, pairing codes, or real camera feeds.

## Website And Docs 🌍

- Confirm website build passes.
- Confirm privacy URL loads: `https://manix84.github.io/ha-tv-pip/privacy/`.
- Confirm release notes in GitHub Release use `WHATSNEW.md`.
- Confirm root README install guidance still starts with user setup, not development instructions.
- Confirm Play Store prep docs are current before uploading an AAB.

