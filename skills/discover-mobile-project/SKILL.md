---
name: discover-mobile-project
description: Discover an existing iOS, Android, Flutter, or React Native repository and produce stable Mobile Engineering Harness project context. Use when attaching the harness, refreshing stale context, or investigating an unfamiliar mobile codebase; do not use for feature-specific requirements or implementation.
---

# Discover Mobile Project

Inspect before changing anything. Prefer repository configuration, build files, CI, tests, and representative neighboring features over assumptions.

Produce `.mobile-harness/context/` with `project-profile.yaml`, `architecture-map.md`, `module-map.yaml`, `conventions.md`, `commands.yaml`, `design-system-map.yaml`, `test-infrastructure.md`, and `risks.md`. Validate the profile against `contracts/project-profile.schema.json` when available.

Record:

- platform, languages, supported OS, modules, dependencies, and adapter;
- source/test/generated paths and architectural boundaries;
- navigation, state, networking, persistence, design system, localization, accessibility, analytics, and flags;
- build, lint, test, and device commands observed in the project;
- freshness inputs and every critical unknown.

Execute only cheap read-only discovery commands. A build command is "known" when it is derived from checked-in configuration; call it "working" only after recorded execution. Classify unknowns as `blocking`, `assumption`, `deferred`, or `resolved`. Stop the discovery gate when adapter, build command, source paths, or critical conventions cannot be established.
