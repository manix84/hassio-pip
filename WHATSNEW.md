# What's New ✨

## 1.31.41 - Receiver Launcher Recovery Fix 🕹️

- Prevented hiding the Android TV launcher icon until receiver pairing is complete 🔐
- Restored the launcher icon automatically when pairing is reset or missing, so setup remains recoverable 📺
- Opened the receiver app automatically when pairing starts so the TV-side pairing code popup appears immediately 🔢

## 1.31.40 - Play Console Screenshot Assets 📱

- Added two Play Console-compatible portrait screenshots for the required generic phone/tablet screenshot slot 📸
- Added a crisp 1280 x 720 Play Store TV banner and updated the Android TV banner resource 📺
- Updated Play Store prep docs with the exact asset paths to upload in Play Console 🧭

## 1.31.39 - Play Store Asset Prep Polish 📺

- Added a product-led 1024 x 500 Play Store feature graphic placeholder 🖼️
- Updated Play Store listing drafts with styled notifications, camera defaults, and compatibility guidance 📝
- Aligned Play Console prep docs with the current screenshots, developer header asset, and manual submission steps ✅

## 1.31.38 - Slideshow Timer Reset Fix ⏱️

- Restarted the screenshot slideshow timer when a user manually selects a slide dot 🎞️
- Kept the selected dot progress fill aligned with the current slide after manual navigation 🟦

## 1.31.37 - Web Screenshot Asset Optimization 🖼️

- Switched photo-like website screenshots and generated visuals to smaller JPEG assets for faster page loads ⚡
- Updated the root README to use optimized homepage PiP screenshots while keeping source PNG captures in docs 📸
- Documented the PNG/JPEG screenshot asset split for website and Play Store preparation 🧭

## 1.31.36 - Website Screenshot Slideshow 🎞️

- Added cropped PiP and full Google TV homepage PiP screenshots to the promotional website 📺
- Replaced the screenshot grid with an automatic slideshow and manual progress-dot controls 🟦
- Added the dashboard and homepage PiP screenshots to the root README as a quick visual promo 🖼️
- Updated screenshot asset documentation for website and Play Store preparation 📸

## 1.31.35 - Website Screenshot Section 📸

- Added a real Android TV receiver dashboard screenshot to the promotional website 🖼️
- Added localized screenshot-section copy across Tier 1 website locales 🌍
- Refreshed the stored dashboard screenshot so it shows the connected receiver state ✅

## 1.31.34 - Play Store Readiness Checklists 📋

- Added Play Console submission, data-safety, app-store asset, and release QA checklists 📺
- Updated Play Store prep docs to separate account/profile assets from product listing assets 🖼️
- Updated README and website status wording for AAB release assets and Play Store readiness 🚀

## 1.31.33 - Website Privacy Page 🔒

- Added a public website privacy policy page suitable for Play Console privacy-policy URL requirements 🌐
- Added the Privacy footer link across Tier 1 website locales 🧭
- Added website tests for privacy route generation and footer translation coverage 🧪

## 1.31.32 - Play Store App Bundle Release Asset 📦

- Added a dedicated Android App Bundle release job for future Play Console upload 🏗️
- Added release asset validation for the generated `.aab` archive shape 🔎
- Updated release and Play Store prep docs to distinguish user-installable APKs from Play Console AAB uploads 📚

## 1.31.31 - Play Store Metadata Drafts 📺

- Added Fastlane-compatible English Play Store listing metadata drafts for the Android TV receiver app 📝
- Added initial internal-test release notes metadata for future Play Console prep 📦
- Updated Play Store prep docs to point at the source-controlled metadata folder 🧭

## 1.31.30 - Version Mismatch Repair Issue 🛠️

- Added a Home Assistant repair issue when a receiver APK version does not match the installed integration version 🧭
- Added Tier 1 translation strings for the version-mismatch repair message 🌍
- Updated roadmap, troubleshooting, and integration docs for the actionable version-alignment workflow 📚

## 1.31.29 - Receiver Version Alignment Diagnostics 🧭

- Added receiver and integration version alignment attributes to Home Assistant receiver status and compatibility diagnostics 🔎
- Reused the integration manifest version helper in config entry diagnostics so HACS/APK drift is reported consistently 🧰
- Updated tests and troubleshooting docs for checking matched beta release installs 🧪

## 1.31.28 - Android Workflow SDK Setup Fix 🛠️

- Removed the obsolete Android SDK `tools` package from release and Android quality workflow setup 🧰
- Kept explicit platform and build-tools installation in place for debug, release, lint, typecheck, test, and dry-run jobs ✅
- Bumped the release so GitHub can publish a clean package after the `1.31.27` debug APK setup failure 🔁

## 1.31.27 - Guided Restream Setup Steps 🧭

- Added ordered setup steps to `ha_tv_pip.suggest_restream_source` so manual go2rtc/Frigate setup has a clear HLS-first, MJPEG-fallback, save-source flow 🧰
- Added a `fallback_test_action` payload for validating the matching MJPEG candidate when the first HLS URL is not TV-safe 🔁
- Updated tests, README, roadmap, and camera compatibility docs for the guided manual restream setup response 📚

## 1.31.26 - Camera Compatibility Docs Alignment 📚

- Updated the root README to mention copyable camera compatibility follow-up action payloads 🧰
- Marked the latest restream helper response improvements as completed in the roadmap ✅
- Kept future WebRTC, automatic provider setup, and transcoding work clearly separated from current manual helper support 🔎

## 1.31.25 - Complete Restream Follow-Up Actions 🎯

- Added copyable Home Assistant `action` keys and receiver targets to restream `next_action` payloads 🧰
- Made saved restream defaults and one-step setup responses easier to paste back into Home Assistant actions 🔁
- Updated integration tests for the complete follow-up action shape 🧪

## 1.31.24 - Copyable Restream Helper Actions 📋

- Added copyable Home Assistant `action` keys to restream helper `save_action` and `test_action` payloads 🧰
- Kept legacy `service` keys for compatibility with existing consumers 🔁
- Updated tests and camera compatibility docs for consistent follow-up action payloads 🧪

## 1.31.23 - Restream Helper Presets 🧭

- Made `suggest_restream_source` expose `go2rtc`, `frigate`, and `manual` helper presets in Home Assistant service metadata 🧰
- Added regression coverage for unknown provider labels falling back to generic manual URL placeholders 🔎
- Aligned README and roadmap wording so manual helper support is marked complete while automatic provider integrations remain future work 📚

## 1.31.22 - Redacted Defaults Summary 🛡️

- Added `defaults_summary` to `ha_tv_pip.save_restream_source` responses so saved provider, stream type, and URL presence can be confirmed without echoing the URL 🔎
- Kept the existing `defaults` response for compatibility while documenting the safer summary field 🧰
- Updated tests and camera compatibility docs for the redacted confirmation payload 🧪

## 1.31.21 - Restream Test Follow-Up 🧪

- Added `test_action` to `ha_tv_pip.suggest_restream_source` responses so users can validate the first suggested HLS candidate without assembling the next service call manually 🧰
- Covered both go2rtc and Frigate helper paths in tests 🔎
- Updated docs for the suggestion-to-validation workflow 📚

## 1.31.20 - Copyable Compatibility Actions 📋

- Added `service_call` payloads to camera compatibility `action_plan` responses so recommended next actions include `action`, `target.device_id`, and `data` 🧰
- Kept the existing `service` and `data` fields for compatibility while making the response easier to paste into Home Assistant actions 🔎
- Updated docs and tests for the richer action-plan payloads 🧪

## 1.31.19 - Frigate Restream Guidance 📹

- Added Frigate as a manual restream helper path alongside go2rtc 🧰
- Made `ha_tv_pip.suggest_restream_source` preserve `restream_provider: frigate` and return Frigate/go2rtc-style HLS/MJPEG candidate URLs 🔎
- Updated provider diagnostics, docs, website copy, and tests for the broader manual restream helper flow 🧪

## 1.31.18 - Guided Setup Steps 🧭

- Added ordered `setup_steps` to `ha_tv_pip.setup_camera` responses so UI helpers and troubleshooting flows can show the next action clearly 🧰
- Included validation details, save actions, and ready-to-use `show_camera` follow-ups in guided restream setup responses 🔎
- Updated docs, website copy, and tests for the richer guided setup response 🧪

## 1.31.17 - Guided Camera Setup 🧭

- Added `ha_tv_pip.setup_camera` as the preferred guided camera setup action for normal calibration and manual restream validation 🧰
- Returned `setup_mode` and `setup_summary` so Home Assistant action responses are easier to follow 🔎
- Updated service metadata, translations, docs, website copy, and tests for the guided setup path 🧪

## 1.31.16 - One-Step Restream Save 🧭

- Added `save: true` to `ha_tv_pip.test_restream_source` so a valid manual restream URL can be tested and saved in one action 🧰
- Returned `saved_as_defaults`, `saved_defaults`, and a minimal `show_camera` next action after a successful validate-and-save call 🔄
- Updated Home Assistant action metadata, translations, docs, and tests for the simpler guided restream workflow 🧪

## 1.31.15 - Saved Defaults Sensor Refresh 🔄

- Made the Saved Camera Defaults sensor refresh immediately when per-camera defaults are saved or cleared 🩺
- Added regression coverage for camera-default update signals so the sensor does not stay stale after `save_restream_source` 🧪

## 1.31.14 - Restream URL Shape Validation 🧭

- Made `ha_tv_pip.test_restream_source` distinguish playable stream endpoints from provider base URLs before recommending a save action 🧪
- Added `url_shape` details to restream validation responses so users can see why a candidate URL should or should not be saved 🔎
- Updated tests and camera compatibility docs for the base-URL validation path 🧰

## 1.31.13 - Restream Source Validation 🧪

- Added `ha_tv_pip.test_restream_source` to validate a candidate manual HLS/MJPEG restream URL before saving it 🧰
- Returned inferred stream type, receiver capability support, optional reachability results, next-step guidance, and a safe `save_restream_source` payload when the candidate looks usable 🔎
- Updated Home Assistant service metadata, tests, and camera compatibility docs for the validate-before-save restream workflow 📹

## 1.31.12 - Restream Base URL Suggestions 🧭

- Added optional `restream_base_url` support to `ha_tv_pip.suggest_restream_source` so candidate HLS/MJPEG URLs can use a real go2rtc host instead of the default placeholder 🧰
- Returned the effective restream base URL in suggestion responses for easier troubleshooting 🔎
- Added Home Assistant service metadata and tests for custom restream base URL suggestions 🧪

## 1.31.11 - Compatibility Guidance Surfacing 🩺

- Added `restream_source_suggestion` to camera compatibility and calibration results when a TV-safe restream source is recommended 🧭
- Moved detailed receiver, compatibility, command-result, and restreaming helper entities into Home Assistant's diagnostic entity category 🧰
- Kept the main Status sensor as the primary receiver state while preserving troubleshooting data on the device page 🔎

## 1.31.10 - Restream Source Suggestions 🧭

- Added `ha_tv_pip.suggest_restream_source` to produce manual go2rtc-style restream setup guidance for a selected camera and receiver 📹
- Returned candidate stream names, candidate HLS/MJPEG URL patterns, provider help, and a follow-up `save_restream_source` action payload 🧰
- Added Home Assistant service metadata, translations, tests, and compatibility docs for the guided restream suggestion flow 🧪

## 1.31.9 - Camera Defaults Cleanup 🧹

- Added `ha_tv_pip.clear_all_camera_defaults` to remove every saved per-camera default from a receiver in one action 🧰
- Returned cleared camera counts and entity IDs so users can confirm exactly what was removed 🔎
- Updated Home Assistant service metadata, translations, tests, and camera compatibility docs for the cleanup flow 🧪

## 1.31.8 - Saved Camera Defaults Visibility 🩺

- Added a Saved Camera Defaults sensor to each receiver device so saved per-camera defaults and restream source counts are visible in Home Assistant 🔎
- Exposed non-sensitive saved camera and restream summary attributes while keeping raw restream URLs hidden from entity attributes 🛡️
- Updated HA tests and docs for the new saved-defaults visibility path 🧪

## 1.31.7 - Restream Source Helper 🧵

- Added `ha_tv_pip.save_restream_source` to save a tested HLS or MJPEG restream URL as per-camera defaults 🧰
- Defaulted the helper flow to `go2rtc`, snapshot fallback on, and inferred HLS/MJPEG stream type when possible 📺
- Added Home Assistant action metadata, translations, docs, and tests for the new restream-source save workflow 🧪

## 1.31.6 - Popup Visual Polish 🪟

- Added Android window background blur for translucent overlay popup backgrounds on supported Android TV devices 🧊
- Cropped HLS, MJPEG, snapshot, and full-screen test video rendering to fill the available container and reduce black bars 📺
- Added an opt-in `text_overlay` media option so camera/snapshot title and message text can sit over the video or image instead of below it 📝
- Kept the blur conditional so fully opaque popup backgrounds avoid unnecessary processing work ⚡

## 1.31.5 - Manual Restream Helper Workflow 🧵

- Added manual go2rtc helper metadata to restreaming provider diagnostics and camera calibration action plans 🧰
- Included example TV-safe HLS/MJPEG URL patterns and the `set_camera_defaults` fields needed to save a working manual restream URL 📺
- Updated camera compatibility docs, roadmap, packaged integration README, and website wording for the larger go2rtc/WebRTC/transcoding compatibility track 📝

## 1.31.4 - Camera Calibration Action Plans 🧭

- Added an `action_plan` block to camera calibration and compatibility results so users can see the next service to call and the data to use 🧰
- Added `primary_action` and `primary_action_label` to calibration summaries for faster interpretation in Home Assistant action responses 🔎
- Made snapshot-only compatibility results point users toward either saved snapshot alerts or a TV-safe live source instead of leaving restreaming guidance as raw fields 🧵

## 1.31.3 - Compact Receiver Options 🧰

- Split the Home Assistant receiver options flow into an everyday defaults screen and an advanced setup screen for popup sizing, position, and remote receiver credentials 🧭
- Preserved existing advanced settings when users save the compact options screen, so normal edits do not accidentally clear remote setup or popup layout defaults 🛡️
- Updated Tier 1 Home Assistant translation files for the new advanced-settings toggle and screen labels 🌍

## 1.31.2 - Discovery Address Repair 🛠️

- Made the existing Zeroconf unique-id update path explicit so rediscovered receivers can repair stored host, port, version, pairing, and API metadata after DHCP address changes 📡
- Added regression coverage for the discovery repair update payload 🧪
- Documented the expected DHCP repair behavior and troubleshooting path for receivers that move to a new IP address 📝

## 1.31.1 - Remote-Aware Status Polling 🩺

- Updated receiver status, display mode, stream type, version, compatibility, connected, remote connected, and launcher visibility polling to use the configured local/remote transport order 🌍
- Added `transport` attributes to polled receiver entities so users can see whether local HTTP or remote WebSocket supplied the latest status 🧭
- Kept launcher hide/show actions local-only while making their status read path remote-aware, because launcher management still requires the TV-local control endpoint 📺

## 1.31.0 - Remote Status Refresh 🔄

- Added a remote WebSocket request/response path so Refresh Status can query connected remote receivers without local LAN access 🌍
- Reused the same Android status payload for local `/status` and remote status responses to keep diagnostics consistent 🩺
- Updated Refresh Status to follow receiver transport preference and record whether `local` or `remote` handled the refresh 🧭

## 1.30.0 - Remote Close PiP 🚪

- Added remote WebSocket support for Close PiP so remote receivers can close active popups without local HTTP access 🌍
- Updated the Android remote receiver client to handle remote close commands and increment remote message diagnostics 📺
- Updated the Home Assistant Close PiP button to follow the same transport preference ordering as Test PiP 🧭

## 1.29.2 - Remote Transport Preference Fixes 🛠️

- Kept the Home Assistant external URL prefilled while allowing options to save with a blank token and remote receiver mode disabled ⚙️
- Made Test PiP follow the configured local-first or remote-first transport preference 🧪
- Kept local HTTP as the default transport while preserving WebSocket fallback when local control fails 🌐

## 1.29.1 - Remote Transport Preference 🌍

- Added a receiver option to prefer remote WebSocket transport while keeping local HTTP first by default ⚙️
- Updated command routing so the preference controls transport ordering: remote-first with local fallback, or local-first with remote fallback 🧭
- Documented future options-screen polish so advanced receiver controls can be hidden or collapsed by default later 📝

## 1.29.0 - Receiver And Remote Health Diagnostics 🩺

- Added Android receiver service runtime diagnostics for foreground state, start count, last start reason, and boot/package-replaced receiver activity 🔄
- Exposed the new service-health block through the local `/status` endpoint and Home Assistant status attributes 🔎
- Added remote receiver connection diagnostics for attempt count, successful connection count, message count, disconnect reason, and connection timestamps 🌍
- Added tests for Android service and remote runtime tracking plus Home Assistant status parsing/entity attributes 🧪
- Updated support docs so reboot/startup issues can be debugged without guessing whether the receiver service actually restarted 📚

## 1.27.14 - Signed APK Install Guidance 📦

- Updated user-facing install docs to recommend the signed release APK from GitHub Releases for normal sideload installs 📺
- Kept the debug APK documented as a troubleshooting and maintainer-requested build rather than the default install path 🧪
- Aligned the root README, Android app README, and packaged Home Assistant integration README with the signed APK release flow 📝

## 1.27.12 - Release Signing Prep 📦

- Added release asset validation so GitHub Releases check APK names, APK archive shape, integration zip layout, HACS zip layout, icons, ignored paths, and manifest version consistency before publishing 🔎
- Split release packaging into clearer workflow jobs for setup, Android debug APK, Android release APK, Home Assistant integration, release asset checks, publishing, and cleanup 🧭
- Prepared Android release signing through GitHub Actions secrets, with signed APK verification when secrets are configured and unsigned fallback for beta validation 🖊️
- Documented the Android signing secret setup and kept keystores/passwords out of git by default 🔐

## 1.27.11 - Compatibility Diagnostics And Stream Strategy 🩺

- Added a Last Command Result sensor so the Home Assistant receiver device shows the latest command type, accepted/failed status, transport, final stream type, failure stage, failure reason, and update time 🧭
- Added redacted last-command diagnostics alongside camera-specific diagnostics 🔎
- Improved receiver compatibility guidance for degraded, legacy, and incompatible receivers so users know when to update the Android app 📺
- Updated automatic camera stream selection so receivers without playable fallback prefer MJPEG first when available, reducing decoder risk without extra automation YAML 🎥

## 1.27.10 - HACS Support And Compatibility Polish 🧰

- Added a Receiver Compatibility sensor so the Home Assistant device shows compatible, degraded, legacy, or incompatible receiver states directly 🩺
- Added integration release metadata and the minimum HACS options-flow baseline to config entry diagnostics 🔎
- Documented `v1.27.9+` as the practical HACS beta baseline for the Configuration screen and added troubleshooting guidance for the earlier `500` options-flow failure 📝
- Added package/release verification notes so future releases check HACS zip layout, options-flow loading, and core receiver diagnostic entities before publishing 📦

## 1.27.9 - Options Flow Dropdown Fix 🧩

- Fixed a Home Assistant options-flow 500 error caused by raw `vol.Any(...)` dropdown schemas that the frontend serializer could not convert 🛠️
- Replaced the receiver defaults stream strategy and popup position fields with Home Assistant `SelectSelector` dropdowns ✅
- Added test coverage for the dropdown helper while keeping the lightweight local test stubs working 🧪

## 1.27.8 - Options Flow Startup Guard 🧩

- Hardened the Home Assistant options flow so it can render even if Home Assistant has not attached the runtime `hass` object before the first options step loads 🛡️
- Added regression coverage for opening the options flow without `hass` available, matching the suspected 500 path on some installations 🧪

## 1.27.7 - Options Flow Compatibility 🧩

- Made the Home Assistant options flow keep its config entry reference directly, improving compatibility with older Home Assistant Core versions when opening the integration Configuration screen 🛠️
- Kept support for newer Home Assistant Core versions that expose `OptionsFlow.config_entry` through the flow manager ✅
- Verified Home Assistant integration linting, type checking, package structure tests, and the full HA test suite 🧪

## 1.27.6 - Config Flow Load Hardening 🧩

- Moved shared stream and popup position constants into the lightweight integration constants module so the config/options flow no longer imports the full service implementation while loading 🛠️
- Kept the HACS zip layout from `1.27.5`, with integration files at the archive root for direct HACS extraction 📦
- Verified Home Assistant integration linting, type checking, and tests after the config-flow cleanup ✅

## 1.27.5 - HACS Zip Install Fix 🧩

- Fixed the stable HACS release zip layout so HACS installs files directly into `config/custom_components/ha_tv_pip/` instead of creating a nested `custom_components/ha_tv_pip/` folder 📦
- Kept the versioned integration zip in manual-install layout with `custom_components/ha_tv_pip/` preserved for users inspecting or unpacking releases manually 🛠️
- Added root-level `icon@2x.png` and `logo@2x.png` integration assets for consistency with the existing brand image set 🎨
- Updated HACS packaging docs to explain the difference between the versioned manual zip and the stable HACS zip 📝

## 1.27.4 - HACS README And Icon Compatibility 🧩

- Moved the install-first APK, integration, and pairing flow into the packaged Home Assistant integration README as well as the root README 📺
- Added root `icon.png` and `logo.png` compatibility aliases alongside the HACS `brand/` assets 🎨
- Documented the HACS presentation asset paths so future packaging changes do not accidentally remove them 📝

## 1.27.3 - HACS Store Presentation Refresh 🧩

- Added root `brand/icon.png` and `brand/logo.png` assets so HACS can pick up repository-level presentation artwork 🎨
- Reworked the root README so HACS users see APK installation, integration installation, and pairing instructions before development details 📺
- Moved monorepo layout, Android Studio, website, and script instructions into a dedicated Development section lower in the README 🛠️

## 1.27.2 - HACS Custom Repository Compliance 🧩

- Moved the Home Assistant integration source to root `custom_components/ha_tv_pip/` so the monorepo is directly HACS-compliant without a duplicated mirror 🧩
- Kept `ha-integration/` for Python tooling, tests, and integration package scripts 🛠️
- Updated release packaging, version checks, tests, and docs for the root HACS layout ✅

## 1.27.0 - Public Beta Support Hardening 🧪

- Added a dedicated troubleshooting guide for discovery, pairing, popup display, stream compatibility, launcher recovery, remote receiver mode, and support data collection 🩺
- Replaced the loose bug report Markdown template with a structured GitHub issue form that asks for receiver version, integration version, Home Assistant version, TV model, camera platform, stream strategy, service YAML, and redacted diagnostics 🐛
- Linked beta support guidance from the root README, Home Assistant integration README, roadmap, development docs, and website footer 📚

## 1.26.0 - Camera Stream Source Visibility 🔎

- Added `stream_source` metadata to compatibility and last-result surfaces so users can see whether a popup used the main camera, alternate stream entity, snapshot entity, or manual restream URL 🔎
- Updated Home Assistant integration docs and tests for the new source classification metadata 🧪

## 1.25.0 - Restream URL Compatibility Bridge 🧵

- Added optional `restream_url` and `restream_provider` fields for camera actions, calibration, compatibility tests, and per-camera defaults so users can point a camera at a TV-safe go2rtc or similar stream today 📹
- Added direct restream URL command handling with snapshot preview support, while keeping normal Home Assistant camera entities as the default path 🎬
- Redacted saved restream URLs from diagnostics and covered request parsing, defaults, command generation, compatibility reports, and diagnostics with tests 🧪

## 1.24.2 - Compatibility Response Provider Hints 🧵

- Added `restreaming_provider` metadata to camera compatibility and calibration responses when restreaming is recommended 🔎
- Added compact provider status and next-step hints to calibration summaries so dashboards can show clearer guidance 🧭
- Updated tests and docs for the expanded compatibility response shape 🧪

## 1.24.1 - Restreaming Guidance Metadata 🧵

- Added current workaround paths and a documentation URL to restreaming provider metadata so diagnostics and sensors point users toward TV-safe stream fixes 🩺
- Exposed provider status, planned providers, current paths, and docs link on the `Camera Restreaming Recommended` binary sensor 🔎
- Updated the camera compatibility docs to separate current HLS/MJPEG/snapshot workarounds from future go2rtc, WebRTC, and transcoding plans 📚

## 1.24.0 - Restreaming Provider Status 🧵

- Added a `Restreaming Provider Status` sensor to the Home Assistant receiver device so future go2rtc, WebRTC, and transcoding support is visible as planned but inactive 🩺
- Centralized restreaming provider metadata so diagnostics and entities report the same provider state 🔧
- Updated Home Assistant translations and tests for the new provider status sensor 🧪

## 1.23.0 - Receiver Diagnostics And Device Plans 📺

- Added the Android receiver release version to the on-device diagnostics panel so support checks can confirm the installed app build quickly 🩺
- Added translated diagnostics labels for the release version across the current Android Tier 1 language resources 🌍
- Reworked the root README current phase section so completed history is collapsed and current compatibility work is easier to scan 📚
- Expanded README and roadmap device support plans with progress markers for supported, next-likely, research, and watchlist TV platforms ✅

## 1.22.2 - Camera Compatibility Guide 🧵

- Added a dedicated camera compatibility guide covering TV-safe streams, calibration, snapshot fallback, and future restreaming provider expectations 📹
- Added an inactive planned restreaming provider block to Home Assistant diagnostics for future go2rtc, WebRTC, and transcoding support 🩺
- Linked the new guide from the root README, development docs, roadmap, Home Assistant integration README, and website copy 📝
- Added diagnostics test coverage for the planned provider structure 🧪

## 1.22.1 - Restreaming Next Steps And Website Accessibility 🧭

- Added `restreaming_next_step` and `restreaming_options` to camera compatibility and calibration results so users get actionable guidance after a failed or snapshot-only live path 🧵
- Exposed the same next-step guidance on the `Camera Restreaming Recommended` binary sensor attributes 🔎
- Updated tests and docs for the expanded restreaming guidance fields 🧪
- Added website accessibility tests for FAQ disclosure controls, theme selector labels, copy feedback, and localized image alt text ♿
- Added a dedicated `website: accessibility` GitHub Actions job while keeping the tests inside `website:test` for pre-commit coverage 🧪
- Animated the FAQ answer reveal and global theme paint changes with CSS transitions, including a reduced-motion fallback ✨

## 1.22.0 - Camera Restreaming Sensor 🧵

- Added a `Camera Restreaming Recommended` binary sensor to the receiver device so snapshot-only or unavailable live stream paths are visible without opening diagnostics 🧭
- Added restreaming attributes to the new sensor, including camera entity, recommendation reason, restreaming reason, and test timestamp 🔎
- Updated translations, docs, and tests for the new visibility path 🧪

## 1.21.2 - Restreaming Guidance Groundwork 🧵

- Added `restreaming_recommended` and `restreaming_reason` to camera compatibility and calibration results so snapshot-only or unavailable live paths point users toward a TV-safe restreamed source 🧭
- Updated calibration summaries to include restreaming guidance without adding unsupported WebRTC or transcoding command types yet 📺
- Documented the future WebRTC, go2rtc, and transcoding path while keeping current support focused on HLS, MJPEG, and snapshots 📝
- Added tests for snapshot-only and no-compatible-stream camera compatibility results 🧪

## 1.21.1 - Camera Defaults Diagnostics 🩺

- Added stored per-camera defaults to Home Assistant diagnostics so calibration and saved stream strategy state are easier to inspect 🩺
- Documented the full camera calibration loop: calibrate without saving, inspect recommended defaults, save defaults, and use `show_camera` without repeating values 🧭
- Added tests for camera defaults diagnostics visibility 🧪

## 1.21.0 - Camera Calibration Action 🧭

- Added `ha_tv_pip.calibrate_camera` as a friendly action for testing a camera/receiver pair and optionally saving the recommended per-camera defaults 🧭
- Added calibration summaries with compatibility status, recommendation reason, save state, and next-step guidance 🧩
- Updated service metadata, translations, docs, website copy, and tests for the calibration workflow 🧪

## 1.20.1 - Recommended Defaults Preview 👀

- Added `recommended_defaults` to `ha_tv_pip.test_camera_stream` responses so users can see exactly what would be saved before enabling `save_recommendation` 👀
- Reused the same defaults builder for preview and save paths so compatibility recommendations cannot drift from saved per-camera defaults ⚙️
- Added tests and documentation for the recommendation preview workflow 🧪

## 1.20.0 - Compatibility Result Sensor 🩺

- Added a `Last Camera Compatibility` receiver sensor so the latest camera test recommendation is visible on the Home Assistant device page 🧭
- Added timestamps to camera compatibility reports so the integration can identify the most recent test result reliably 🕒
- Updated tests, translations, docs, and website copy for the new compatibility visibility path 🧪

## 1.19.0 - Save Camera Recommendations ⚙️

- Added `save_recommendation` to `ha_tv_pip.test_camera_stream` so a successful compatibility test can store the recommended stream strategy as a per-camera default 🧭
- Saved explicit test fields such as width, height, duration, position, snapshot fallback, and stream/snapshot entities alongside the recommendation when provided ⚙️
- Updated service metadata, translations, docs, and tests for the recommendation-saving workflow 🧪

## 1.18.0 - Camera Result Diagnostics 🔎

- Added a `Last Camera Result` receiver sensor showing the latest camera/snapshot command outcome without exposing stream URLs 🩺
- Stored redacted command outcome diagnostics with requested stream type, final stream type, transport, fallback usage, size, and failure reason when available 🔐
- Added clearer `ha_tv_pip.test_camera_stream` recommendation reasons, including when `auto`, `mjpeg_first`, HLS, MJPEG, or snapshot is the best next default 📹

## 1.17.0 - Receiver Compatibility Checks 🧩

- Added a computed receiver compatibility summary for compatible, degraded, legacy, and incompatible receiver states 🧩
- Exposed receiver compatibility state, missing features, and warnings through Home Assistant status attributes and diagnostics 🔎
- Gracefully downgrade camera and snapshot popups when a receiver cannot render title/message footers, while preserving media playback and sizing where possible 📺

## 1.16.0 - Camera Compatibility Defaults 🧭

- Added `ha_tv_pip.test_camera_stream` to check HLS, MJPEG, and snapshot availability for a camera/receiver pair 🧪
- Added `ha_tv_pip.set_camera_defaults` and `ha_tv_pip.clear_camera_defaults` for per-camera stream strategy, substream, snapshot, duration, position, width, and height defaults ⚙️
- Stored non-sensitive last camera compatibility results in Home Assistant diagnostics 🔎
- Updated website and docs for camera compatibility testing and per-camera defaults 📝

## 1.15.0 - Receiver Action Defaults ⚙️

- Added Home Assistant receiver options for preferred stream strategy, default duration, popup position, snapshot fallback, width, and height ⚙️
- Made `ha_tv_pip.show_camera`, `ha_tv_pip.show_snapshot`, and `ha_tv_pip.show_notification` use receiver defaults only when the action does not provide its own value 🏠
- Updated HA action metadata so UI-mode actions can omit fields and rely on receiver defaults cleanly 🧭

## 1.14.0 - Receiver Visibility Entities 🧰

- Added focused Home Assistant sensors for active display mode, active stream type, last receiver error, and receiver app version 🔎
- Added a remote-connected binary sensor and a refresh-status button for receiver troubleshooting 🧰

## 1.13.1 - Capability-Aware Stream Selection 🧭

- Used receiver-reported capabilities to reject unsupported forced stream, snapshot, notification, and media-text commands before sending them 🛡️
- Updated automatic stream selection to skip unsupported receiver formats and only send playable fallback URLs when the receiver supports them 📺
- Refreshed troubleshooting and promotional wording around receiver capability checks 📚

## 1.13.0 - Home Assistant Capability Parsing 🏠

- Parsed Android receiver capability metadata into a typed Home Assistant status model 🧭
- Exposed supported stream types, notification positions, and receiver feature flags on the status sensor for troubleshooting 🔎

## 1.12.0 - Receiver Capability Metadata 🧭

- Added receiver capability metadata to Android `/` and `/status` responses so clients can see supported command features without guessing 🧭
- Documented receiver capabilities for local API users and troubleshooting tools 📚

## 1.11.0 - Fallback Playback Diagnostics 🔎

- Added fallback stream URL/type fields to Android receiver playback status so stream-fallback decisions are visible in `/status` 🔎
- Updated receiver status documentation to describe playable fallback diagnostics 📺

## 1.10.0 - Diagnostics Redaction 🔐

- Recursively redacted receiver diagnostics for stream URLs, preview URLs, fallback URLs, remote URLs, and tokens 🔐
- Added tests so future stream diagnostics fields do not leak private camera or Home Assistant URLs 🧪

## 1.8.0 - Receiver-Side Stream Fallback 📺

- Added optional playable fallback media fields so automatic HLS commands can carry an MJPEG fallback URL 📹
- Updated the Android overlay receiver to switch from failed HLS playback to MJPEG when a fallback stream is provided 🔁
- Added tests for Home Assistant payloads and Android command parsing for fallback stream fields 🧪

## 1.7.0 - Receiver Playback Diagnostics 🔎

- Added nested Android receiver playback diagnostics to `/status`, including preview URL and update time 🔎
- Hardened MJPEG playback with bounded frame reads and explicit snapshot/MJPEG network timeouts 📺

## 1.6.0 - Stream Preference And Diagnostics 📹

- Added `stream_type: mjpeg_first` so camera alerts can prefer MJPEG, then fall back to HLS and snapshot if needed 📺
- Kept `stream_type: mjpeg` as a strict force-MJPEG option for advanced troubleshooting 🧪
- Updated Home Assistant service metadata, tests, and docs for the new stream preference option 📝

## 1.4.1 - Target Selection And Stream Fallback 🎯

- Rejected non-device Home Assistant targets with a clear HA TV PiP validation error instead of generic schema failures 🎯
- Improved `stream_type: auto` so Home Assistant tries MJPEG before falling back to snapshots when HLS URL resolution fails 📹
- Updated docs and website FAQ wording for the new HLS to MJPEG to snapshot fallback order 📝

## 1.3.0 - Stream Compatibility 📹

- Added optional `stream_camera_entity` support so camera alerts can use a more compatible live-stream entity while keeping the primary camera for titles and snapshot fallback 📹
- Added explicit `stream_type: mjpeg` support using Home Assistant's camera proxy stream endpoint and receiver-side MJPEG overlay rendering 📺
- Added receiver status reporting for the active stream type so MJPEG tests are easier to diagnose 🔎
- Updated unsupported-stream guidance to suggest compatible substreams, H.264, or `stream_type: mjpeg` 🩺
- Added a copyable website example for MJPEG fallback automations 🌐
- Standardized receiver selection on Home Assistant `target.device_id` and removed the duplicate `receiver_device_id` service field 🎯
- Updated Home Assistant service metadata, Tier 1 translation labels, tests, and docs for separate stream camera selection 🏠

## 0.48.0 - Stage 12 Release Hardening 📦

- Added explicit debug and release Android APK assets to GitHub release packaging 📺
- Updated release docs for immutable GitHub Releases and draft-first asset publishing 📦
- Added Stage 11 enhanced notification examples to the website and automation examples 🔔
- Expanded HACS-facing integration README install, setup, service, option, and limitation guidance 🧩
- Published the first Stage 12 GitHub release candidate with Android debug APK, Android release APK, versioned integration zip, and stable HACS zip ✅

## 0.47.0 - Release Workflow Fix 📦

- Changed release automation to attach assets while the GitHub Release is still a draft so published immutable releases are not mutated 📦
- Documented that already-published failed releases must be deleted manually or replaced by bumping to the next version 📝

## 0.46.0 - Stage 12 Planning 📦

- Defined Stage 12 as beta release hardening instead of a new feature stage 🚧
- Added release-candidate goals for full checks, Android builds, HACS zip validation, website build validation, and release packaging ✅
- Updated root, Android, Home Assistant, website, examples, roadmap, development, Play Store, and official Home Assistant readiness docs 📝
- Updated the website locale status content so public pages point to Stage 12 and beta-readiness work 🌍
- Marked Tier 1 translations complete and Tier 2/Tier 3 translations planned across docs and the website 🌐

## 0.45.0 - Stage 11 Complete ✅

- Completed Stage 11 enhanced notifications after Chromecast manual testing 📺
- Added explicit receiver support for title-only media notification footers without requiring a message 🔔
- Kept resize-only camera and snapshot commands clean so width/height do not accidentally show a text footer 📐
- Stacked video or snapshot media above notification text inside one continuous rounded glass popup ✨
- Added translucent alpha-hex background support for glass-style notification overlays 🎨
- Added useful Home Assistant service field examples without forcing examples on receiver/entity selectors 🏠
- Expanded HA and Android tests for notification payloads, title-only footers, resize-only media, and service metadata 🧪

## 0.41.0 - Stage 11 Enhanced Notifications 🔔

- Started Stage 11 with `ha_tv_pip.show_notification` for styled TV text alerts 🏠
- Added Android receiver parsing for `streamType: notification` commands 📺
- Added Android overlay rendering for notification title, message, corner position, colors, text sizes, and duration 🎨
- Allowed camera and snapshot popups to include the same optional notification text and styling fields 📹
- Rounded the TV notification card corners so alert overlays feel less harsh 📺
- Added optional `width` and `height` fields for notification, camera, and snapshot overlays 📐
- Reused both local HTTP and remote WebSocket receiver transports for notification commands 🌍
- Added Home Assistant service metadata, translations, validation, and focused tests ✅

## 0.39.1 - Phase 10 Distribution Polish 🎨

- Started a TV-first receiver dashboard with summary cards, primary PiP controls, launcher controls, remote receiver settings, and diagnostics separated from everyday actions 📺
- Moved verbose endpoint, discovery, and compatibility details into a dedicated diagnostics section 🧰
- Improved D-pad startup focus by keeping `Play Test Video` in the first action group 🎮
- Added Home Assistant-assisted remote receiver config sync and made manual URL/token entry an advanced fallback 🔐
- Hid manual remote receiver fields behind an advanced setup action so normal TV setup stays cleaner 📺
- Added Tier 1 website locale content modules with browser language detection and manual language override 🌍
- Documented the Stage 10 decision to keep onboarding, pairing, and troubleshooting as dashboard sections instead of separate TV screens 🧭
- Added a TV-side pairing popup that prominently shows the active Home Assistant pairing code 📺
- Added glass-style dashboard cards with stronger TV focus treatment ✨
- Made dashboard sections selectable containers so D-pad navigation can move from section to controls and back more predictably 🎮
- Added confirmation warnings before `Reset Pairing` and `Clear Remote` run destructive actions ⚠️
- Completed manual Android TV D-pad testing on the receiver dashboard ✅
- Added root `hacs.json` for HACS zip-release installation 🧩
- Added a stable `ha-tv-pip-integration.zip` release asset for HACS while keeping the versioned integration zip 📦
- Added HACS custom-repository install docs 📝
- Changed release automation to run on pushes to `main`, creating or updating the versioned GitHub Release with Android and HACS assets 🚀
- Added Play Store release-prep materials covering listing copy, privacy wording, screenshots, signing, and release notes 📺
- Added Android release App Bundle build scripts for Play Store prep 📦
- Added official Home Assistant integration readiness checklist 🏠
- Documented future enhanced-notification overlay options for position, title, message, colors, and text sizes 🔔

## 0.28.0 - Phase 9 Documentation And FAQ Polish 📚

- Marked Phase 9 remote receiver transport as complete in the roadmap ✅
- Added website FAQ content for setup worries, stream compatibility, remote mode, and translations ❓
- Added translation planning for Android, Home Assistant, and website language support 🌍
- Added extra remote transport fallback and runtime-state tests 🧪

## 0.27.0 - Phase 9 Remote Receiver Transport 🌍

- Added Home Assistant WebSocket registration for outbound remote receivers 🏠
- Added Android TV remote receiver client settings for Home Assistant external URL and long-lived access token 📺
- Sent remote `show_camera` and `show_snapshot` commands over the receiver's outbound WebSocket connection when connected 🔔
- Kept local HTTP control as the fallback when no remote receiver connection is active 🏠
- Kept HA TV PiP local-first: this is not a hosted HA TV PiP cloud service ✅

## 0.26.0 - Stage 8 Receiver Management Extension 🧰

- Added a Hide Launcher switch for Home Assistant 🏠
- Added an Open Launcher button so Home Assistant can reopen the app after the launcher icon is hidden 📺
- Added authenticated receiver management endpoints for opening the app and showing or hiding the launcher icon 🔐
- Added Android boot and package-replaced startup handling so the local receiver service starts without manually opening the app after restart 🔄

## 0.25.0 - Stage 8 Receiver Entities 🩺

- Added receiver status and connected entities for Home Assistant dashboards 🏠
- Added receiver test and close buttons for quick receiver management 🎛️
- Added diagnostics output with token and stream URL redaction 🔐
- Added typed receiver client helpers for `/status` and `/close` 📡
- Confirmed receiver entities appear correctly in Home Assistant ✅

## 0.24.0 - Stage 7 Stream Type Options 🎛️

- Added `stream_type: auto`, `stream_type: hls`, and `stream_type: snapshot` to `ha_tv_pip.show_camera` 🏠
- Made automatic mode prefer HLS and fall back to a snapshot command when Home Assistant cannot resolve a stream 🖼️
- Kept receiver snapshot previews visible when video playback fails after the stream URL is accepted 📺
- Logged the selected stream type before sending receiver commands 📺
- Confirmed the Chromecast fallback path shows a snapshot with a small fallback message instead of a black box ✅

## 0.23.0 - Snapshot Fallback Previews 🖼️

- Added optional entity-based snapshot fallback previews while video streams load 🏠
- Let `ha_tv_pip.show_camera` use `snapshot_camera_entity` for a separate preview camera entity 📷
- Updated the receiver protocol to accept `previewUrl` and replace the preview with live video when playback is ready 📺

## 0.22.0 - Stage 6 Snapshot Support 🖼️

- Added `ha_tv_pip.show_snapshot` to display camera snapshots from Home Assistant 🏠
- Added Android TV snapshot overlay rendering for `streamType: snapshot` 📺
- Reused pairing, bearer-token auth, receiver targeting, and duration timeouts for snapshots 🔐
- Confirmed camera feeds and snapshot feeds both work on the Chromecast test receiver ✅

## 0.21.2 - Generic Stream Error Wording 🩺

- Generalised unsupported-stream messages so they are not tied to one camera brand or setup 📺
- Updated docs to describe codec/profile compatibility in vendor-neutral terms 🧭

## 0.21.1 - Stage 5 Stream Compatibility Polish 🎞️

- Added receiver-side decoder fallback before reporting unsupported stream failures 📺
- Added clearer TV overlay feedback for unsupported camera streams 🩺
- Documented that broad main-stream support needs future stream selection, restreaming, or transcoding 🧭

## 0.21.0 - Stage 5 Service MVP 📹

- Added the first `ha_tv_pip.show_camera` service implementation 🏠
- Resolves Home Assistant camera HLS stream URLs and sends them to paired receivers 🎬
- Added service schema metadata for the Home Assistant UI 🧭
- Added focused service and receiver-client tests 🧪
- Verified the service path with a compatible lower-resolution camera stream on Chromecast 📺
- Added receiver playback diagnostics for unsupported stream codec errors 🩺
- Enabled Media3 decoder fallback for receiver playback before reporting unsupported codec failures 🎞️

## 0.18.0 - Stage 4 Complete 🔐

- Completed local pairing hardening for the Android TV receiver ✅
- Prevented remote clients from replacing an existing pairing without TV-side reset 🛡️
- Refreshed mDNS discovery metadata when pairing state changes 🔎
- Documented the Stage 4 pairing flow and reset process 📝
- Excluded `.DS_Store` files from packaged integration zips 📦

## 0.17.1 - Brand Icons And Pairing Polish 🎨

- Added Home Assistant custom integration brand images under `custom_components/ha_tv_pip/brand/` 🏠
- Confirmed Home Assistant shows the integration icon after restart 🧩
- Kept the direct integration `icon.png` and `logo.png` assets for compatibility 📁

## 0.17.0 - Local Receiver Pairing 🤝

- Added `/pair/start` and `/pair/confirm` endpoints to the Android TV receiver 🔐
- Showed the pairing code on the TV instead of exposing it in normal setup UX 📺
- Required bearer-token auth for `/show` and `/close` once pairing is required or complete 🛡️
- Added Home Assistant config-flow pairing and token storage 🏠
- Added a TV-side `Reset Pairing` action 🔁

## 0.14.1 - Confirmation Modal Polish 🧭

- Added a visible receiver-name field to the discovery confirmation modal so it is no longer blank 📝
- Kept the discovered receiver name as the default confirmation value 📺

## 0.14.0 - Device Page And Shared Icon 🧩

- Registered discovered receivers in Home Assistant's device registry so they have a device page 🏠
- Added explicit confirmation form schema and English translations for the discovery confirmation screen 📝
- Added a shared PNG project icon for Android, Home Assistant, and the website 🎨
- Lowered successful Zeroconf flow diagnostics back to debug logging after discovery validation 🪵

## 0.12.0 - Discovery Confirmation Flow 🔎

- Changed Zeroconf discovery to show a confirmation card instead of auto-creating entries 🧭
- Added confirmation text for discovered receivers 📝
- Kept manual host/port setup as a fallback path only 🛟

## 0.11.0 - Discovery Diagnostics 🔎

- Switched the Home Assistant Zeroconf manifest matcher to the explicit object format 🧭
- Added temporary warning-level Zeroconf flow diagnostics so HA logs show whether discovery reaches the integration 🪵
- Kept manual receiver setup as a fallback, not the primary path 🛟

## 0.10.0 - Manual Receiver Setup 🧭

- Added manual Home Assistant setup for receiver host and port 🏠
- Kept Zeroconf discovery as the preferred setup path 🔎
- Added manual setup validation and tests for fallback receiver entries 🧪

## 0.9.0 - Config Flow Load Fix 🧭

- Added a manual setup step that cleanly explains discovery-only setup 🏠
- Removed the runtime dependency on Home Assistant's Zeroconf type location 🔧
- Added config-flow helper coverage and Home Assistant strings for early abort reasons 🧪

## 0.8.1 - Home Assistant Entry Lifecycle 🧩

The Home Assistant scaffold can now load and unload discovered config entries cleanly.

- Added initial `async_setup_entry` and `async_unload_entry` lifecycle hooks 🏠
- Added async tests for config entry setup and unload behavior 🧪
- Kept receiver clients, entities, services, pairing, and authentication out of scope for this slice 🔒

## 0.8.0 - Home Assistant Discovery Scaffold 🏠

Stage 3 now has the first Home Assistant-side discovery scaffold.

- Added Home Assistant integration manifest with version sync and Zeroconf matching 🔎
- Added a config-flow entry point for HA TV PiP receiver discovery 🧭
- Added typed discovery payload parsing for receiver id, host, port, name, version, pairing state, and API version 🪪
- Added tests for Android TXT-record parsing and fallback defaults 🧪
- Confirmed the release zip now packages the integration files under `custom_components/ha_tv_pip/` 📦
- Kept TV control from Home Assistant, pairing, and authentication out of scope for this slice 🔒

## 0.7.0 - Stage 3 Discovery Begins 🔎

Stage 3 starts with Android-side local network discovery advertising.

- Added Android NSD / mDNS advertisement for `_ha-tv-pip._tcp.local.` 📡
- Added discovery metadata for device id, receiver name, app version, pairing state, and API version 🪪
- Added discovery state to `GET /status` responses 🩺
- Added discovery status to the Android TV main screen 📺
- Added unit coverage for discovery descriptors and runtime state 🧪
- Kept Home Assistant Zeroconf config flow, pairing, and authentication out of scope for this slice 🔒

## 0.6.0 - Stage 2 Endpoint Hardening 🛠️

The local control endpoint now handles the first round of real-device hardening after Chromecast validation.

- Enforced `durationSeconds` for the overlay fallback path ⏱️
- Added duplicate `/show` replacement feedback in API responses 🔁
- Added local endpoint address display on the Android TV main screen 📍
- Added `apiVersion` and `controlPort` to `/status` responses 📡
- Added endpoint uptime, request count, and previous request diagnostics to `/status` 🩺
- Added live endpoint diagnostics to the Android TV main screen 📺
- Added `GET /` API metadata plus JSON `404` and `405` error responses 🧭
- Added defensive local IP detection and endpoint display tests 🧪

## 0.5.0 - Stage 2 Local Control Begins 🌐

Stage 2 has started with a developer-testable local HTTP endpoint in the Android TV app.

- Added local receiver service on port `8765` 🛰️
- Added `GET /status` for version, device, playback, and display-mode state 📡
- Added `POST /show` for HLS playback commands 🎬
- Added `POST /close` for stopping playback and overlay fallback 🛑
- Added duplicate `/show` replacement feedback and overlay auto-close timing ⏱️
- Added the local endpoint address to the Android TV main screen 📍
- Added command validation and JVM unit tests for show requests 🧪
- Kept pairing, authentication, discovery, and Home Assistant integration out of scope for now 🔒

## 0.4.0 - Chromecast Overlay Validation 📺

Phase 1 is now validated on physical Chromecast with Google TV hardware.

- Added device compatibility detection for native PiP and overlay support 🧭
- Added a no-ADB floating overlay fallback for Google TV devices that reject native PiP 🪟
- Added an overlay permission entry point from the Android TV app UI 🔐
- Added overlay stop handling from the receiver main screen 🛑
- Updated the player action label so fallback devices show `Show Overlay` instead of `Enter PiP` 🎮
- Confirmed the fallback works on Chromecast with Google TV after granting overlay permission ✅

## 0.3.0 - Phase 1 Complete ✅

Phase 1 is now complete and validated as the Android TV PiP MVP.

- Confirmed Android TV Kotlin receiver app builds successfully 📺
- Confirmed Media3 / ExoPlayer public HLS playback path compiles cleanly 🎬
- Confirmed manual and Home-triggered PiP support is implemented 🪟
- Added Android, Home Assistant integration, and website test coverage 🧪
- Added split GitHub Actions quality jobs for linting, type checking, tests, and dry-run builds ✅
- Added native Git pre-commit checks and version bump automation 🪝
- Added local dependency installer with Android SDK detection and Home Assistant Python virtualenv setup 🛠️
- Added GitHub Pages-ready promotional website build 🌐
- Updated Android SDK/build tools configuration for Android Studio 2026.1.1 / SDK 36.1 compatibility 🤖

## 0.1.0 - Phase 1 MVP 🚀

Initial Android TV Picture-in-Picture proof of concept.

- Added Android TV Kotlin app 📺
- Added Media3 / ExoPlayer HLS playback 🎬
- Added public test stream playback 🧪
- Added manual `Enter PiP` control 🪟
- Added automatic PiP entry when Home is pressed 🏠
- Added structured Android logging 🪵
- Added root monorepo layout for future Android app and Home Assistant integration work 🧱
- Added placeholder Home Assistant integration directory 🚧
- Added package metadata and version consistency checks 📌
- Added GitHub Release packaging for Android APK and Home Assistant integration zip 📦
- Added pre-commit semantic version bump automation 🔢
- Added promotional Vite website scaffold 🌐

## Not Included Yet 🛑

- Home Assistant integration
- Camera support
- Pairing
- Discovery
- Authentication
- Cloud connectivity
- Remote access
- WebRTC
