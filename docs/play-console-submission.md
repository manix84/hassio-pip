# Play Console Submission Checklist 📺

This checklist is for the first Google Play Console submission of the Android TV receiver app. It assumes GitHub Releases remain the public install path until Play Console review and testing are complete.

## Current Blocker 🚧

Google developer account verification must finish before the first app can be created and submitted.

Do not upload app bundles, create tester tracks, or enter production listing data until the account is fully verified.

## App Creation Values 🧾

Use these values when creating the first Play Console app:

- App name: `HA TV PiP Receiver`
- Default language: English.
- App or game: App.
- Free or paid: Free.
- Package name: `com.hatvpip.receiver`.
- Distribution target: Android TV / Google TV.
- Initial release track: Internal testing.

The current source-controlled listing metadata is under `android-tv-app/fastlane/metadata/android/en-US/`. If the Play Console default language is changed later, add matching metadata folders rather than editing only the Console.

## Store Listing Fields 📝

Source-controlled drafts:

- Title: `android-tv-app/fastlane/metadata/android/en-US/title.txt`
- Short description: `android-tv-app/fastlane/metadata/android/en-US/short_description.txt`
- Full description: `android-tv-app/fastlane/metadata/android/en-US/full_description.txt`
- Internal-test release notes: `android-tv-app/fastlane/metadata/android/en-US/changelogs/default.txt`

Suggested Play Console values:

- Category: House & Home if available for Android TV; otherwise Tools.
- Website: `https://manix84.github.io/ha-tv-pip/`
- Privacy policy: `https://manix84.github.io/ha-tv-pip/privacy/`
- Support email: TODO, choose the public support address to use for Play users.
- Tags/positioning: Home Assistant, Android TV, Google TV, smart home, security camera, Picture-in-Picture, local-first.

Keep the Play listing product-led. Personal profile graphics can be used for the developer profile or account banner, but the app listing should use the HA TV PiP icon, TV banner, feature graphic, and receiver screenshots.

## Release Artifact 📦

Upload the Android App Bundle from the latest GitHub Release:

```txt
ha-tv-pip-android-release-vX.Y.Z.aab
```

Do not upload the APK to Play Console. APKs remain useful for sideloading and debug installs from GitHub Releases.

Before upload:

1. Confirm the release version matches root `package.json`.
2. Confirm the GitHub Release includes the signed release APK, debug APK, AAB, and Home Assistant integration zips.
3. Confirm the Android receiver version and HACS integration version match.
4. Confirm `npm run check` passed before the release was published.

## App Access And Reviewer Notes 🔎

Recommended app access answer:

```txt
The app launches without an account and shows a local Android TV receiver dashboard. Full camera popup functionality requires a Home Assistant instance with the HA TV PiP custom integration installed and paired with the receiver on the same network, or remote receiver mode configured through the user's own Home Assistant external URL.
```

Reviewer notes:

```txt
Open the app on Android TV to see the receiver dashboard, service state, pairing controls, and test PiP controls. The app does not require a HA TV PiP cloud account. It is controlled by a Home Assistant custom integration after local pairing.
```

If Google requires a complete end-to-end account test, prepare a temporary Home Assistant test instance, disposable pairing credentials, and a public non-sensitive camera/test stream before submission.

## App Content Forms 🛡️

Use `docs/play-store-data-safety.md` as the working data-safety answer sheet.

Expected answers for the current app:

- Ads: No.
- Data collection: No data collected by the developer.
- Data sharing: No data shared by the developer.
- App access: App opens without an account; full control requires user's Home Assistant setup.
- Target audience: General smart-home users; not directed at children.
- Content rating: Utility/smart-home app with no user-generated public content, gambling, violence, or mature content.
- News app: No.
- Government app: No.
- Financial features: No.
- Health features: No.

Re-check these answers before each submission if analytics, crash reporting, hosted relay, payment, account, or cloud features are added.

## Testing Track Plan 🧪

Recommended order:

1. Internal testing with your own devices first.
2. Closed testing with trusted Home Assistant / Android TV users.
3. Wider beta only after camera compatibility and setup docs are stable.
4. Production release after Play policy, install flow, and support readiness are proven.

For personal developer accounts, Google may require a closed-testing period before production access. Track this in the Play Console once the account is verified.

## Manual Steps After Verification ✅

1. Create the Play Console app.
2. Enter the listing text from Fastlane metadata.
3. Add the privacy URL.
4. Complete data-safety, content-rating, app-access, and target-audience forms.
5. Upload the latest release AAB to internal testing.
6. Add internal testers.
7. Run the pre-release QA checklist from `docs/release-qa.md`.
8. Submit the internal test build.
9. Record any Play warnings or policy questions in `docs/play-store.md`.

