# HA TV PiP Website 🌐

[![Website Quality 🌐](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/quality-website.yml) [![Website Deploy 🌍](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml/badge.svg)](https://github.com/manix84/ha-tv-pip/actions/workflows/website.yml)

Promotional Vite website for HA TV PiP.

The site currently acts as the project landing page, documentation entry point, FAQ, roadmap preview, and translation-aware promotional surface. Stage 12 documentation work includes keeping the website current with beta release hardening, release-candidate status, and Stage 11 notification examples.

## Tech Stack 🛠️

- Vite
- React
- TypeScript
- SCSS Modules

## Development 🚀

From the monorepo root:

```sh
npm run website:dev
```

From this directory:

```sh
npm run dev
```

## Build 📦

```sh
npm run build
```

The site is static and deploys to GitHub Pages from the website workflow on pushes to `main`.

## Quality Checks ✅

```sh
npm run lint
npm run typecheck
npm run test
npm run build
```

The website uses ESLint for React/TypeScript linting, `tsc --noEmit` for type checking, and Vitest for tests.
The build command is also used as the website dry-run build in the Website Quality workflow.

## Deployment 🌍

The GitHub Actions website workflow builds the site on pull requests and deploys `website/dist` to GitHub Pages on pushes to `main`.

## Version 📌

The displayed version comes from the root `package.json` at build time through `vite.config.ts`.

## FAQ And Translations 🌍

The landing page includes a FAQ for setup concerns, privacy expectations, remote receiver mode, and common stream compatibility questions.

Translation planning is documented in `../docs/translations.md`. The Phase 10 polish pass added Tier 1 static locale routes and localized TypeScript content modules without adding a heavy framework or backend.
