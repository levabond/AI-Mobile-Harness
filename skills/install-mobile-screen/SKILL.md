---
name: install-mobile-screen
description: Install a complete production-ready mobile screen into an existing app, including state, navigation, previews or fixtures, tests, and integration. Use for a new end-to-end screen; do not use for small edits to an existing screen or a standalone visual mockup.
---

# Install Mobile Screen

Start from the approved brief and plan. Find the closest screen and follow its module ownership, state model, route registration, dependency injection, design-system, accessibility, localization, analytics, preview, and test conventions.

Install the entire screen contract: entry route, exit/back behavior, loading, content, empty when applicable, recoverable error, retry, lifecycle-safe async work, accessibility identifiers, and preview/fixture data. Keep visual code thin around testable state and actions. Avoid placeholders that compile but leave navigation or production data wiring disconnected.

Add unit tests for state transitions and a project-native UI/smoke test when the adapter supports it. Record unsupported runtime checks instead of simulating them. Finish with a scoped diff review and development summary; verification, QA, and review remain separate gates.
