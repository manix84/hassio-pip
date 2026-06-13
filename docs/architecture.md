# Architecture

HA TV PiP is planned as a local-first system with two main parts:

- Android TV receiver app.
- Home Assistant custom integration.

Phase 1 only implements the Android TV receiver app. It has no Home Assistant integration and no network control plane.

## Android TV App

The Android app is responsible for video playback and Android Picture-in-Picture behavior. The Phase 1 implementation uses Media3 ExoPlayer with a public HLS stream to validate playback and PiP lifecycle handling.

Future phases should keep playback, receiver control, and pairing concerns separate so camera sources can be added without rewriting PiP behavior.

## Home Assistant Integration

The integration will be added later under `ha-integration/custom_components/ha_tv_pip/`. It is expected to provide discovery, pairing, configuration, and services for sending camera display commands to paired Android TV devices.
