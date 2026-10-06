---
name: discover-mobile-feature
description: Turn a mobile feature request into an evidence-backed brief, acceptance criteria, scope, risks, and explicit uncertainties. Use before planning a feature or substantial behavior change; do not use for repository-wide discovery or begin implementation.
---

# Discover Mobile Feature

This skill is a mobile specialization of the required upstream `superpowers:brainstorming` process. Invoke and follow that Superpowers skill first; this file only adds mobile questions and artifact contracts. If Superpowers is unavailable, stop with a setup blocker rather than silently substituting an ad-hoc interview.

Load current project context and investigate relevant routes, neighboring features, design-system elements, API/persistence contracts, tests, analytics, and flags before asking questions.

Write `rnd/feature-brief.yaml`, `rnd/acceptance-criteria.yaml`, and, when material, dependency map, assumptions, open questions, risk register, and decision log. Use `contracts/feature-brief.schema.json` and `contracts/acceptance-criteria.schema.json`.

Cover user value, entry/exit flow, loading/content/empty/error/offline/recovery states, data ownership, module integration, accessibility, localization, lifecycle, privacy, performance, rollout, and explicit out-of-scope behavior. Ask only unresolved questions that change the result. Group them, identify blocking questions, and offer safe defaults for non-blocking ones.

Record `spike`, `bounded`, or `architectural` classification and explicit design approval in the brief. Do not pass the R&D gate until Superpowers' approval gate is satisfied, every must acceptance criterion is observable, affected modules are identified, mandatory states are described, and no `blocking` uncertainty remains.
