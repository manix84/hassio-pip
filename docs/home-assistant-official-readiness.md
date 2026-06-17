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
- Tier 2 and Tier 3 translation expansion planned after beta hardening.
- Tests for config flow helpers, discovery parsing, receiver client behavior, entities, services, remote setup, and remote transport.
- Brand assets included in the custom integration package.

## HACS Readiness ✅

- Root `hacs.json` exists.
- HACS uses `zip_release`.
- Release workflow uploads `ha-tv-pip-integration.zip`.
- Zip internal path is `custom_components/ha_tv_pip/`.
- Integration `manifest.json` includes required HACS-facing metadata.
- Brand directory includes `icon.png`.

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

## Non-Goals For Stage 10 🚧

- Submitting to Home Assistant core.
- Moving files into the Home Assistant core repository.
- Removing HACS custom-repository support.
- Blocking Android TV receiver development on official-integration acceptance.

## Suggested Next Steps 🧭

1. Complete Stage 12 beta release hardening first.
2. Add Hassfest validation workflow.
3. Add a Home Assistant dev-container or documented test environment.
4. Audit config flow and entity classes against the latest Home Assistant integration quality scale.
5. Write Home Assistant documentation pages for discovery, pairing, services, remote receiver mode, and troubleshooting.
6. Decide whether official inclusion should happen before or after broader stream compatibility work.
