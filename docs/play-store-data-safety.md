# Play Store Data Safety Draft 🛡️

This document is the working answer sheet for the Google Play data-safety form. Re-check it before every Play submission.

## Current Summary ✅

For the current Android TV receiver:

- The app does not collect personal data for the developer.
- The app does not share personal data with third parties for the developer.
- The app does not include ads.
- The app does not include analytics SDKs.
- The app does not include crash-reporting SDKs.
- The app does not create a HA TV PiP cloud account.
- The app does not upload camera streams, snapshots, pairing tokens, usage events, or diagnostics to HA TV PiP maintainers.

## Data Collection Answers 🧾

Expected current answers:

- Location: No.
- Personal info: No.
- Financial info: No.
- Health and fitness: No.
- Messages: No.
- Photos and videos: No.
- Audio files: No.
- Files and docs: No.
- Calendar: No.
- Contacts: No.
- App activity: No.
- Web browsing: No.
- App info and performance: No developer collection.
- Device or other IDs: No developer collection.

Android system logs may contain local debug information on the user's device. The app does not upload those logs to maintainers.

## Local Processing And Storage 🔐

The app uses local data to provide the receiver experience:

- Pairing token and receiver settings are stored locally on the Android TV device.
- Remote receiver URL/token settings can be stored locally when the user configures remote receiver mode.
- Home Assistant stores paired receiver configuration and service defaults in the user's Home Assistant instance.
- Camera stream and snapshot URLs are loaded only to display the requested popup.

This local processing is not developer collection under the current implementation because HA TV PiP maintainers do not receive the data.

## Network Behavior 🌐

The app uses network access for:

- Local receiver control from Home Assistant.
- mDNS / local-network discovery.
- Loading camera HLS, MJPEG, snapshot, and notification media URLs requested by Home Assistant.
- Optional outbound remote receiver WebSocket connection to the user's own Home Assistant external URL.

HA TV PiP does not run a hosted relay service.

## Security Practices 🔒

Current safety posture:

- Local pairing is required before Home Assistant can control a receiver.
- Remote receiver mode requires a Home Assistant URL and access token supplied by the user.
- Overlay permission is user-granted and used for TV popup display fallback.
- No third-party analytics or advertising SDKs are present.

Review this document before adding:

- Cloud relay features.
- Hosted account features.
- Analytics.
- Crash reporting.
- Remote logging.
- Payment or subscription functionality.
- Any third-party SDK that processes user data.

