# Repository guidance

- Preserve the evidence-before-claims invariant: a passed executable check must reference a recorded command, exit code, and log.
- Treat `methodology/` as normative. R&D requires `superpowers:brainstorming`; verification requires `superpowers:verification-before-completion`, with `superpowers:systematic-debugging` on failure.
- Route Apple build, test, simulator/device, log, and UI-automation work through MobileBuildMCP unless a fixture explicitly declares hermetic native fallback.
- Keep orchestration platform-independent. Platform commands belong in adapters.
- Do not add runtime dependencies without explicit approval; the reference CLI uses the Python standard library.
- Treat `evals/fixtures/` as test applications. Product changes there must be paired with an eval or contract update.
- Keep stable rules here. Put task-specific multi-step procedures in `skills/*/SKILL.md`.
- Do not edit generated files or `.mobile-harness/runs/` by hand.
