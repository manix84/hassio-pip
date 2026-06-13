# Contributing 🛠️

Thanks for helping improve HA TV PiP.

## Current Focus 🎯

The project is currently in Phase 1:

- Android TV Kotlin app.
- Test HLS playback.
- Picture-in-Picture reliability.
- Clean monorepo structure.

Please do not add Home Assistant integration, discovery, pairing, authentication, camera support, or cloud features until the project moves into a later phase.

## Development Setup 💻

Open the Android app from:

```sh
android-tv-app/
```

Build from the command line:

```sh
cd android-tv-app
./gradlew assembleDebug
```

You need JDK 17 or newer and the Android SDK installed.

## Pull Requests 📬

Good pull requests should:

- Stay focused on one change.
- Include clear testing notes.
- Avoid unrelated formatting churn.
- Keep future Home Assistant work behind documentation or placeholders until that phase starts.

## Style Notes ✨

- Kotlin first.
- Gradle Kotlin DSL.
- Keep architecture simple and easy to extend.
- Prefer local-first designs for future control and discovery work.
- Emoji are welcome in docs when they make the tone friendlier.
