# Translations 🌍

HA TV PiP should be designed for translation across the Android TV app, Home Assistant integration, and website.

English is the source language and the default locale for all project areas.

The main implementation pass for translations happened during Phase 10 distribution polish. Tier 1 languages are implemented across the Android app, Home Assistant integration, and website. Tier 2 and Tier 3 languages are planned after the Post-v1.0 compatibility surfaces settle and broader testing is available.

---

# Goals ✅

- Keep setup and troubleshooting understandable for non-English users.
- Avoid hard-coded user-facing strings in new Android app UI.
- Use Home Assistant's translation system for config flows, services, entities, diagnostics labels, and repairs where supported.
- Prepare the website for static i18n without adding a heavy framework.
- Keep technical terms consistent across the app, integration, and website.

---

# Language Priority 🗺️

## Tier 1 ✅ Complete

Implemented first during the Phase 10 polish/release pass:

- English
- German
- Dutch
- French
- Spanish
- Italian
- Portuguese, Brazil first
- Polish

## Tier 2 🚧 Planned

Very worth adding after Tier 1 is stable and the Post-v1.0 compatibility surfaces settle:

- Swedish
- Norwegian
- Danish
- Finnish
- Czech
- Hungarian
- Turkish
- Japanese
- Korean

## Tier 3 🚧 Planned

Broader Android and global reach after the core release:

- Simplified Chinese
- Traditional Chinese
- Indonesian
- Hindi
- Arabic
- Ukrainian
- Romanian
- Greek

---

# Android TV App 🤖

Android should use platform string resources.

Current status:

- `app_name` is already in `res/values/strings.xml`.
- Main dashboard strings are now in `res/values/strings.xml`.
- Player screen, playback status, notification, compatibility, overlay fallback, setup guidance, and troubleshooting strings are now in Android resources.
- ✅ Tier 1 Android resource folders now exist for German, Dutch, French, Spanish, Italian, Brazilian Portuguese, and Polish.
- 🚧 Tier 2 and Tier 3 Android resource folders are planned after the Post-v1.0 compatibility surfaces settle.

Required during Post-v1.0 compatibility polish:

- Move any remaining user-facing Compose or Android framework strings into `res/values/strings.xml`.
- Keep the Tier 1 resource folders complete as new user-facing strings are added.
- Keep logs and internal protocol strings in English unless they are shown directly to users.
- Make sure TV remote navigation labels, error messages, and recovery instructions are translated.
- Validate that translated strings fit on Android TV at common 1080p and 4K font scales.

---

# Home Assistant Integration 🏠

Home Assistant should use integration translation files.

Current status:

- English config-flow strings exist in `strings.json` and `translations/en.json`.
- ✅ Tier 1 translation files exist for config-flow and options-flow strings.
- ✅ Entity names expose translation keys with Tier 1 translated names.
- ✅ Service names, descriptions, and field labels are mirrored into translation metadata with Tier 1 labels.
- 🚧 Tier 2 and Tier 3 Home Assistant translation files are planned after the Post-v1.0 compatibility surfaces settle.
- Diagnostics wording should be expanded as the integration matures.

Required during Post-v1.0 compatibility polish:

- Keep `translations/en.json` as the source translation file.
- Keep Tier 1 translation files under `custom_components/ha_tv_pip/translations/` complete as new strings are added.
- Translate service fields, entity labels, diagnostics, and repair messages where Home Assistant exposes supported translation surfaces.
- Keep `iot_class: local_push`; remote receiver mode must not be described as a HA TV PiP cloud service.
- Avoid translating internal service names such as `ha_tv_pip.show_camera`.

---

# Website 🌐

The website should support static translated pages without becoming a full documentation platform.

Preferred approach during Post-v1.0 website polish:

- Keep the current English single-page site as the source.
- Add lightweight locale content modules when translation work starts.
- Generate static locale routes such as `/de/`, `/nl/`, and `/pt-br/`.
- Keep GitHub Pages deployment simple.
- Do not add analytics or authentication for translation support.

Current Post-v1.0 status:

- ✅ Tier 1 locale routes are detected client-side.
- ✅ Website language selection prefers the URL locale, then the user's saved override, then browser language detection.
- ✅ Users can override the detected language from the website language selector.
- ✅ The website build creates `dist/de/`, `dist/nl/`, `dist/fr/`, `dist/es/`, `dist/it/`, `dist/pt-br/`, and `dist/pl/` entry points for GitHub Pages.
- ✅ Tier 1 website copy exists in separate TypeScript locale modules.
- 🚧 Tier 2 and Tier 3 website locale routes are planned after the Post-v1.0 compatibility surfaces settle.
- Native-speaker review is skipped for Stage 10 because it is not currently available. Future community/native review should happen before broad public release where possible.

Website translation content now covered:

- Hero and project summary.
- FAQ.
- Setup/status messaging.
- Roadmap summary.
- Privacy and local-first messaging.
- Release and install links.

---

# Translation Workflow 🧰

Recommended workflow:

1. Finish the English source copy for a feature.
2. Move strings into the correct platform translation system.
3. Add or update Tier 1 translations first.
4. Run quality checks.
5. Manually check long translated strings on small TV and mobile website layouts.
6. Release with Tier 1 translations in place.
7. Add Tier 2 and Tier 3 languages after the Post-v1.0 compatibility surfaces and release path are stable.

Translation contributions should preserve technical accuracy over literal phrasing.

---

# Glossary 📚

Use consistent translations for these concepts:

- Receiver
- Picture-in-Picture / PiP
- Snapshot
- Camera stream
- Pairing
- Launcher
- Remote receiver
- Local-first
- Home Assistant external URL

The glossary should be expanded as translated files are added.
