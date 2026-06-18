# Official Home Assistant Readiness 🏠

This document tracks long-term readiness for proposing HA TV PiP as an official Home Assistant integration. It does not make the integration official and should not block HACS custom-repository distribution.

## Current Position 🚦

HA TV PiP is currently a custom integration.

Near-term distribution target:

```txt
HACS custom repository
```

Long-term target:

```txt
Official Home Assistant integration readiness
```

## Already Aligned ✅

- Local-first design.
- `iot_class: local_push`.
- Config flow support.
- Zeroconf discovery.
- Pairing flow with TV-visible code.
- Bearer-token authentication for receiver commands.
- Diagnostics with token and stream URL redaction.
- Entity registry support for receiver status and controls.
- Entity translation keys.
- Service schema for camera and snapshot commands.
- Tier 1 translation files complete for current integration surfaces.
- Tier 2 and Tier 3 translation expansion planned after the Post-v1.0 compatibility surfaces settle.
- Tests for config flow helpers, discovery parsing, receiver client behavior, entities, services, remote setup, and remote transport.
- Brand assets included in the custom integration package.

## HACS Readiness ✅

- Root `hacs.json` exists.
- HACS uses `zip_release`.
- Release workflow uploads `ha-tv-pip-integration.zip`.
- Stable HACS zip contains the integration files at archive root because HACS extracts `zip_release` assets directly into `config/custom_components/ha_tv_pip/`.
- Versioned manual-install zip preserves the `custom_components/ha_tv_pip/` path.
- Integration `manifest.json` includes required HACS-facing metadata.
- Root `brand/` directory includes HACS-facing `icon.png` and `logo.png`.
- Root `icon.png` and `logo.png` compatibility aliases exist for older/simple HACS presentation paths.
- Installed integration `custom_components/ha_tv_pip/brand/` includes Home Assistant-facing icon and logo assets.
- Root README starts with HACS install guidance because HACS renders the repository README for the store page.

## Official Integration Gaps ⏳

These need a deeper pass before an upstream Home Assistant proposal:

- Confirm code style and architecture against current Home Assistant developer documentation.
- Add Hassfest validation in CI.
- Run Home Assistant's official quality checks against the integration.
- Replace or justify test fallbacks that simulate Home Assistant imports outside a full Home Assistant test harness.
- Review dependency policy and confirm no unsupported runtime dependency pattern.
- Confirm config entry options, repairs, diagnostics, and entity categories match current Home Assistant UX expectations.
- Add native-speaker review for translations where possible.
- Produce user-facing documentation suitable for Home Assistant docs.
- Prepare a migration plan from custom integration installs to official integration installs.
- Confirm naming, domain, icon, and brand assets against Home Assistant project conventions.

## HACS vs Official Integration Packaging 📦

The current custom integration source lives at:

```txt
custom_components/ha_tv_pip/
```

That layout is intentionally HACS-friendly. If HA TV PiP moves toward official Home Assistant inclusion, the official integration will eventually need to live inside Home Assistant core's own integration tree rather than this repository's `custom_components/` tree.

Before that transition, decide whether the project should maintain:

- One shared source tree with a release/export process for HACS and an upstream contribution branch for Home Assistant core.
- Two development folders when HACS-specific and official-core-specific requirements diverge too far.
- Two release builds if HACS needs custom assets, migration helpers, or compatibility shims that would not belong in Home Assistant core.

Likely differences to track:

- HACS requires root `hacs.json`, GitHub release assets, and custom-repository install/update documentation.
- Official Home Assistant core will require upstream repository layout, Home Assistant review standards, Hassfest validation, quality-scale expectations, core docs, and a migration story for existing HACS users.
- HACS can move faster and carry beta compatibility helpers; official core should be more conservative about APIs, dependencies, and maintenance burden.
- HACS and official builds may need different README/install wording, release notes, branding paths, and deprecation guidance.

For now, keep one source tree and document any HACS-only behavior clearly. Revisit separate packaging or folders only when official-core preparation reveals concrete differences that cannot be handled cleanly by packaging.

## Non-Goals For Stage 10 🚧

- Submitting to Home Assistant core.
- Moving files into the Home Assistant core repository.
- Removing HACS custom-repository support.
- Blocking Android TV receiver development on official-integration acceptance.

## Suggested Next Steps 🧭

1. Add Hassfest validation workflow.
2. Add a Home Assistant dev-container or documented test environment.
3. Audit config flow and entity classes against the latest Home Assistant integration quality scale.
4. Write Home Assistant documentation pages for discovery, pairing, services, remote receiver mode, and troubleshooting.
5. Decide whether official inclusion should happen before or after broader stream compatibility work.
