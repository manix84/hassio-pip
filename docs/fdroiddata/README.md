# F-Droid Data Submission

This folder contains the draft metadata for submitting HA TV PiP Receiver to the F-Droid main repository.

Target file in an `fdroiddata` fork:

```txt
metadata/com.hatvpip.receiver.yml
```

Copy from this repository:

```sh
cp docs/fdroiddata/metadata/com.hatvpip.receiver.yml /path/to/fdroiddata/metadata/com.hatvpip.receiver.yml
```

## Merge Request

Suggested branch:

```txt
new-app-com.hatvpip.receiver
```

Suggested commit message:

```txt
New App: HA TV PiP Receiver
```

Suggested merge request title:

```txt
New App: HA TV PiP Receiver
```

Suggested merge request description:

```md
Adds HA TV PiP Receiver, an Android TV companion receiver for Home Assistant camera streams, snapshots, and notifications.

The app is MIT licensed, built from public source, and does not include Google Play services, Firebase, analytics, advertising, billing, or crash-reporting SDKs.

The metadata uses reproducible-build verification against the signed GitHub release APK:

- `Binaries: https://github.com/manix84/ha-tv-pip/releases/download/v%v/ha-tv-pip-android-release-v%v.apk`
- `AllowedAPKSigningKeys: 0607b6647534f792578736382b977853b09449e48c7c651ec1d6a9828073f951`

Local validation performed with fdroidserver 2.4.5:

- `fdroid lint com.hatvpip.receiver`
- `fdroid checkupdates --allow-dirty com.hatvpip.receiver`
- `fdroid build -v -l --test --force com.hatvpip.receiver`
```

## Validation Evidence

Step 4 local validation succeeded for:

```txt
Package: com.hatvpip.receiver
Version: 1.31.45
Version code: 1031045
Tag: v1.31.45
```

The first local validation build completed successfully with the APK at:

```txt
app/build/outputs/apk/release/app-release-unsigned.apk
```

The reviewer-requested metadata removes the explicit `output` and uses `subdir: android-tv-app/app`, so F-Droid can use the default APK output under the module build directory.

The updated local F-Droid test build succeeded with reproducible verification:

- built `1.31.44` from `65e1e1b34a6252a6075224ae57ca7691900483a8`
- retrieved `https://github.com/manix84/ha-tv-pip/releases/download/v1.31.44/ha-tv-pip-android-release-v1.31.44.apk`
- compared the built APK to the supplied reference binary successfully
- confirmed allowed signer `0607b6647534f792578736382b977853b09449e48c7c651ec1d6a9828073f951`

F-Droid rejected the signed `v1.31.44` APK because Android Gradle dependency metadata added APK signing block `0x504B4453` (`Dependency metadata`).

The `v1.31.45` release disables dependency metadata for both APK and App Bundle outputs:

```kotlin
dependenciesInfo {
    includeInApk = false
    includeInBundle = false
}
```

Local validation for the replacement release:

- `npm run version:check`
- `npm run version:android-code:check`
- `npm run fdroid:changelog:check`
- `npm run check`
- `npm run android:assemble:release`
- `npm run android:bundle:release`

A locally temp-signed `1.31.45` release APK no longer contained the rejected `Dependency metadata` APK signing block. It only showed APK signature scheme blocks and verity padding.
