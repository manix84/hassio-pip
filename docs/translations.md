# Translations 🌍

HA TV PiP should be designed for translation across the Android TV app, Home Assistant integration, and website.

English is the source language and the default locale for all project areas.

The main implementation pass for translations belongs to Phase 10 distribution polish. Tier 1 languages should be in place before a broad release. Tier 2 and Tier 3 languages can be added after that as the project matures.

---

# Goals ✅

- Keep setup and troubleshooting understandable for non-English users.
- Avoid hard-coded user-facing strings in new Android app UI.
- Use Home Assistant's translation system for config flows, services, entities, diagnostics labels, and repairs where supported.
- Prepare the website for static i18n without adding a heavy framework.
- Keep technical terms consistent across the app, integration, and website.

---

# Language Priority 🗺️

## Tier 1

Do these first during the Phase 10 polish/release pass:

- English
- German
- Dutch
- French
- Spanish
- Italian
- Portuguese, Brazil first
- Polish

## Tier 2

Very worth adding after Tier 1 is stable:

- Swedish
- Norwegian
- Danish
- Finnish
- Czech
- Hungarian
- Turkish
- Japanese
- Korean

## Tier 3

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
- Many MVP and development strings are still hard-coded in Kotlin Compose UI.

Required during Phase 10 before broad release:

- Move user-facing Compose strings into `res/values/strings.xml`.
- Add translated resource folders, for example `values-de`, `values-nl`, and `values-pt-rBR`.
- Keep logs and internal protocol strings in English unless they are shown directly to users.
- Make sure TV remote navigation labels, error messages, and recovery instructions are translated.
- Validate that translated strings fit on Android TV at common 1080p and 4K font scales.

---

# Home Assistant Integration 🏠

Home Assistant should use integration translation files.

Current status:

- English config-flow strings exist in `strings.json` and `translations/en.json`.
- Service descriptions, entity names, and diagnostics wording should be expanded as the integration matures.

Required during Phase 10 before HACS readiness:

- Keep `translations/en.json` as the source translation file.
- Add Tier 1 translation files under `custom_components/ha_tv_pip/translations/`.
- Translate config flow titles, descriptions, error messages, entity labels, service fields, and repair messages.
- Keep `iot_class: local_push`; remote receiver mode must not be described as a HA TV PiP cloud service.
- Avoid translating internal service names such as `ha_tv_pip.show_camera`.

---

# Website 🌐

The website should support static translated pages without becoming a full documentation platform.

Preferred approach during the Phase 10 website polish pass:

- Keep the current English single-page site as the source.
- Add lightweight locale content modules when translation work starts.
- Generate static locale routes such as `/de/`, `/nl/`, and `/pt-br/`.
- Keep GitHub Pages deployment simple.
- Do not add analytics or authentication for translation support.

Required website translation content:

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
7. Add Tier 2 and Tier 3 languages after the initial polished release.

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
