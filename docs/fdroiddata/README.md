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

Local validation performed with fdroidserver 2.4.5:

- `fdroid lint com.hatvpip.receiver`
- `fdroid checkupdates --allow-dirty com.hatvpip.receiver`
- `fdroid build -v -l com.hatvpip.receiver`

The initial submission uses standard F-Droid signing. Developer-signed reproducible builds are intentionally deferred until after the first source build is accepted.
```

## Validation Evidence

Step 4 local validation succeeded for:

```txt
Package: com.hatvpip.receiver
Version: 1.31.44
Version code: 1031044
Tag: v1.31.44
```

The local F-Droid build completed successfully after adding the explicit output path:

```txt
app/build/outputs/apk/release/app-release-unsigned.apk
```
