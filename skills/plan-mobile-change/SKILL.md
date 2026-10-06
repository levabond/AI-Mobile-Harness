---
name: plan-mobile-change
description: Plan a scoped mobile change from approved discovery artifacts, including files, sequence, tests, evidence commands, rollback, and risk coverage. Use when requirements are ready for development; do not use while blocking product questions remain or to implement the change.
---

# Plan Mobile Change

Read project context, feature brief, acceptance criteria, risks, and the closest existing implementation. Produce `plan/implementation-plan.yaml` conforming to `contracts/implementation-plan.schema.json`.

Describe the project-native design, affected modules, expected files, ordered implementation steps, testing strategy, executable verification operations, rollback, and risks. Set a scope budget with allowed modules, protected paths, expected file count, and a larger replan threshold.

Map every must acceptance criterion to at least one step and every material risk to a planned check. Identify dependency additions, public API changes, migrations, privacy changes, destructive actions, or release operations as approval points. Do not invent unavailable adapter capabilities; mark them unsupported and adjust the plan or profile transparently.
