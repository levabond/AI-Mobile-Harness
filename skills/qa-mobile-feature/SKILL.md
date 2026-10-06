---
name: qa-mobile-feature
description: Test a user-visible mobile feature against its acceptance criteria and risks across functional, recovery, lifecycle, device, accessibility, and integration scenarios. Use after a verifiable build exists; do not use as a substitute for unit verification or code review.
---

# Qa Mobile Feature

Derive a risk-based test plan from the brief, acceptance criteria, risk register, changed diff, and relevant defect history. Use the adapter only for supported device operations.

Exercise happy, alternate, cancel/back, repeat, invalid, loading, empty, error, retry, offline, session, background/foreground, process restoration, screen-size, font-scaling, screen-reader, long-string, theme, permission, deep-link, and feature-flag scenarios when relevant. Match device coverage to the selected profile.

Write `qa/result.yaml` conforming to `contracts/qa-result.schema.json`. Every scenario is `passed`, `failed`, `skipped`, or `not_run` and references evidence or a reason. A defect includes environment, preconditions, steps, expected/actual result, reproducibility, severity, evidence, and only clearly labeled code-area hypotheses. Do not pass the gate with blocking defects or unexplained required skips; record residual risk explicitly.
