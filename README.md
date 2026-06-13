# HA TV PiP 📺🪟

HA TV PiP is a planned Home Assistant companion project for showing short-lived camera feeds on Android TV and Google TV devices using Android Picture-in-Picture.

This repository is a monorepo that will contain both sides of the project:

- `android-tv-app/`: Android TV Kotlin app 📱
- `ha-integration/`: Home Assistant custom integration 🏠
- `docs/`: Architecture, roadmap, and development notes 📚
- `examples/`: Example Home Assistant automations ⚙️

## Current Phase 🧪

Phase 1 is limited to the Android TV MVP. It proves that an Android TV app can play a public HLS test stream and reliably enter and exit Picture-in-Picture mode.

The Home Assistant integration, local control endpoint, discovery, pairing, authentication, camera support, snapshots, and WebRTC support are not implemented yet.

## Monorepo Layout 🧱

```txt
ha-tv-pip/
├── android-tv-app/
│   └── Android TV Kotlin app
├── ha-integration/
│   └── custom_components/ha_tv_pip/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── development.md
├── examples/
│   └── home-assistant-automations/
├── README.md
├── LICENSE
└── .gitignore
```

## Run the Android TV App 🚀

1. Open `android-tv-app/` in Android Studio.
2. Let Android Studio sync Gradle.
3. Select an Android TV or Google TV device, or create an Android TV emulator.
4. Run the `app` configuration.
5. Select `Play Test Video`, then use `Enter PiP` or press Home to test Picture-in-Picture.

From VSCode or a terminal with a configured JDK and Android SDK:

```sh
npm run android:assemble
```

Useful repo scripts:

```sh
npm run check
npm run android:assemble
npm run android:lint
npm run android:clean
```

## Future Home Assistant Plan 🏠

Future phases will add a Home Assistant custom integration and Android TV receiver control features:

- Local HTTP control endpoint 🌐
- mDNS discovery 🔎
- Device pairing 🤝
- Home Assistant config flow 🧭
- Home Assistant service: `ha_tv_pip.show_camera` 📹
- HLS streams from Home Assistant 🎬
- Snapshots and WebRTC support 🖼️
