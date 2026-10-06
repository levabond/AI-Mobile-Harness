---
name: verify-mobile-change
description: Execute technical verification for a mobile change and map real command evidence to required checks and acceptance criteria. Use after implementation or when asked to prove build/test readiness; do not use for semantic code review or silently repair failures.
---

# Verify Mobile Change

Invoke and follow `superpowers:verification-before-completion` for this stage. If any executable check fails, switch to `superpowers:systematic-debugging` before proposing or applying a fix. These upstream methods are required, not optional guidance.

Load the selected profile, adapter capabilities, implementation plan, acceptance criteria, and current diff. Execute the profile's build, lint/static analysis, unit, integration, UI, contract, and repository checks through the adapter.

For Apple builds, tests, simulator/device work, logs, and UI automation, use MobileBuildMCP. Prefer MCP tools during interactive agent work; use its CLI backend when the harness must retain deterministic command metadata. A native Swift command is allowed only for an explicitly declared hermetic fixture fallback.

For every command, retain provider, arguments, working directory, timestamps, exit code, and redacted log. Mark unavailable capability `unsupported`, unexecuted work `not_run`, and an allowed omission `skipped` with its reason. Never infer `passed` from source inspection or an earlier run.

Write `verification/result.yaml` conforming to `contracts/verification-result.schema.json`. Link every acceptance criterion to concrete evidence, detect protected/generated/secret/scope violations, and create structured blocking findings for required checks that are not passed. Diagnose failures, but only edit and retry when the user or workflow explicitly authorizes a bounded repair loop.
