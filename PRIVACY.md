# Privacy Policy 🔒

HA TV PiP is pre-release local-first software. It does not collect, sell, or share personal data with the project maintainers.

## Current Phase 🧪

The Android TV app can play HLS streams and snapshots, advertise itself on the local network, accept paired local commands from Home Assistant, and optionally connect outbound to the user's own Home Assistant external URL for remote receiver mode. It does not use analytics, telemetry, a HA TV PiP cloud relay, or maintainer-operated services.

## Data Collection 📦

The project maintainers receive no app telemetry or usage data.

The Android app may write local Android log messages for development and debugging, including playback state, PiP state, pairing state, request paths, and errors. Pairing tokens are not logged. These logs stay on the Android device unless a developer manually exports them with Android tooling.

## Network Access 🌐

The Android app uses network access to load configured HLS streams and snapshots, advertise and serve its local control endpoint on the LAN, receive paired local commands, and optionally maintain an outbound WebSocket connection to the user's own Home Assistant instance for remote receiver mode.

The Home Assistant integration stores receiver host, port, device id, receiver name, version, pairing state, API version, and a local bearer token in Home Assistant config entry data. Camera stream and snapshot URLs are resolved inside Home Assistant and sent to paired receivers when the user triggers a service.

## Future Phases 🚧

Current development includes Home Assistant camera stream playback, snapshots, and optional remote receiver mode. Remote receiver mode connects the Android TV app outbound to the user's own Home Assistant external URL; HA TV PiP does not operate a hosted cloud relay. Privacy behavior should be updated again before WebRTC or any third-party relay feature is released.

The intended direction is local-first control with no cloud relay by default.
