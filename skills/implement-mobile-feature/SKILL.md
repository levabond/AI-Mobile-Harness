---
name: implement-mobile-feature
description: Implement an approved mobile feature plan in an existing project with tests, fixtures, and a bounded change set. Use for feature development after discovery and planning; do not use for an isolated full-screen installation when install-mobile-screen is the narrower match, or for review-only requests.
---

# Implement Mobile Feature

Load the project context and implementation plan, check the working tree, and inspect the nearest project-native analog. Keep edits inside allowed modules and preserve unrelated user changes.

Implement in small coherent portions. Reuse the project's architecture, design system, navigation, state, dependency injection, networking, persistence, localization, analytics, and test conventions. Cover every planned state and acceptance criterion. Do not add dependencies, change public APIs, migrate data, or alter privacy behavior without the recorded approval required by policy.

Run cheap relevant checks during development. Add behavior-focused tests and fixtures, then self-review the complete diff. Record `dev/development-summary.md`, `dev/deviations.yaml`, changed files, executed commands, and any deferred step. Exceeding the scope budget requires a replan rather than silent expansion. Completion remains provisional until the separate verification gate runs.
