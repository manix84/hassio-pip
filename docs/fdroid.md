# F-Droid Release Prep

This document tracks the F-Droid release path for the HA TV PiP Android TV receiver.

## Release Model

F-Droid main repository releases are not uploaded from this repository in the same way Play Console AABs are uploaded. F-Droid builds APKs from public source using metadata in `fdroiddata`.

Once HA TV PiP is accepted into `fdroiddata`, future releases can be automated by:

1. Bumping the app version and Android `versionCode`.
2. Updating the F-Droid changelog file for that `versionCode`.
3. Tagging the release as `vX.Y.Z`.
4. Letting F-Droid's updater detect the tag and open or apply the next build metadata update.

## Upstream Metadata

F-Droid reads Fastlane-style upstream metadata from:

```txt
android-tv-app/fastlane/metadata/android/en-US/
```

Current metadata includes:

- `title.txt`
- `short_description.txt`
- `full_description.txt`
- `images/icon.png`
- `images/featureGraphic.jpg`
- `images/tvBanner.png`
- `images/phoneScreenshots/`
- `images/tvScreenshots/`
- `changelogs/<versionCode>.txt`

F-Droid changelog files must be named after the Android `versionCode` and stay under 500 characters.

Generate or refresh the current changelog with:

```sh
npm run fdroid:changelog
```

Check release readiness with:

```sh
npm run fdroid:changelog:check
```

The GitHub release workflow runs the check before building release artifacts.

## Draft fdroiddata Metadata

Initial metadata is tracked in this repository at:

```txt
docs/fdroiddata/metadata/com.hatvpip.receiver.yml
```

Copy it into a fork of `fdroiddata` at:

```txt
metadata/com.hatvpip.receiver.yml
```

## Signing

F-Droid verifies the source build against the developer-signed GitHub release APK. The `fdroiddata` metadata includes:

- `Binaries`, pointing at `https://github.com/manix84/ha-tv-pip/releases/download/v%v/ha-tv-pip-android-release-v%v.apk`
- `AllowedAPKSigningKeys`, set to the SHA-256 certificate fingerprint from the release APK

Keep the Android release signing key backed up and private. If the key is lost, F-Droid reproducible verification for future updates cannot continue with the same signing identity.

### Reproducible Build Metadata

The first F-Droid submission includes reproducible-build metadata because F-Droid cannot enable it later for the same app.

The build block uses:

- A full git commit hash instead of a tag or branch.
- `subdir: android-tv-app/app`, the module path where the Gradle `build` directory is generated.
- No explicit `output`, so F-Droid uses the default APK output under the module build directory.

The release APK signer fingerprint is:

```txt
0607b6647534f792578736382b977853b09449e48c7c651ec1d6a9828073f951
```

## Submission Checklist

- Confirm the release commit is tagged as `vX.Y.Z`.
- Confirm `npm run fdroid:changelog:check` passes.
- Confirm the GitHub release includes a signed `ha-tv-pip-android-release-vX.Y.Z.apk`.
- Confirm `AllowedAPKSigningKeys` matches the release APK signer fingerprint.
- Confirm the signed release APK does not include F-Droid's rejected `Dependency metadata` APK signing block.
- Confirm the Play Store AAB still builds with `includeInBundle = false`.
- Fork `fdroiddata`.
- Copy `docs/fdroiddata/metadata/com.hatvpip.receiver.yml` to `metadata/com.hatvpip.receiver.yml` in the `fdroiddata` fork.
- Run `fdroid lint com.hatvpip.receiver`.
- Run `fdroid checkupdates --allow-dirty com.hatvpip.receiver`.
- Run or let GitLab CI run `fdroid build com.hatvpip.receiver`.
- Open a merge request against `fdroid/fdroiddata`.

## Local Validation Notes

Step 4 local validation for `1.31.44` used a temporary `fdroiddata` checkout and `fdroidserver 2.4.5`.

Validated commands:

```sh
fdroid lint com.hatvpip.receiver
fdroid checkupdates --allow-dirty com.hatvpip.receiver
fdroid build -v -l com.hatvpip.receiver
```

Results:

- `fdroid lint com.hatvpip.receiver` passed.
- `fdroid checkupdates --allow-dirty com.hatvpip.receiver` exited successfully. The local `fdroiddata` config printed unrelated `serverwebroot` environment warnings.
- `fdroid build -v -l com.hatvpip.receiver` built `1.31.44` successfully from tag `v1.31.44`.
- `apksigner verify --print-certs` against the GitHub release APK reported SHA-256 fingerprint `0607b6647534f792578736382b977853b09449e48c7c651ec1d6a9828073f951`.
- After reviewer feedback, `fdroid build -v -l --test --force com.hatvpip.receiver` also passed with full commit hash `65e1e1b34a6252a6075224ae57ca7691900483a8`, `subdir: android-tv-app/app`, no explicit `output`, `Binaries`, and `AllowedAPKSigningKeys`.
- The reproducible-build check compared the built APK to the supplied GitHub release APK successfully and reported the allowed signer fingerprint.
- F-Droid rejected the signed `v1.31.44` APK because it contained APK signing block `0x504B4453` (`Dependency metadata`).
- `v1.31.45` disables Android Gradle dependency metadata for APKs and bundles with `dependenciesInfo { includeInApk = false; includeInBundle = false }`.
- A locally temp-signed `1.31.45` release APK no longer contained the rejected `Dependency metadata` signing block. It only showed the APK signature scheme blocks and verity padding.
- `npm run android:bundle:release` passed for `1.31.45`, so the Play Store AAB path remains valid.

Local setup notes:

- The pip-installed `fdroidserver` package did not include `gradlew-fdroid`, so local validation used the helper from `https://gitlab.com/fdroid/gradlew-fdroid`.
- Docker was installed but not running locally, so the official container/buildserver route was not used.
- The F-Droid scanner removed the checked-in Gradle wrapper as expected; the build succeeded through F-Droid's own Gradle helper.
