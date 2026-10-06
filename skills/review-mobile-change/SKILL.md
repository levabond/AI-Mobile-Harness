---
name: review-mobile-change
description: Review a mobile change against its brief, architecture, diff, risks, and tests, returning located structured findings. Use for a post-implementation code review; do not use to implement fixes unless the user separately requests them.
---

# Review Mobile Change

Review the actual diff plus relevant surrounding code. Check behavior, architecture boundaries, state transitions, concurrency/cancellation, lifecycle and memory, errors, API compatibility, persistence/migrations, performance, accessibility, privacy/security, test sufficiency, readability, and scope discipline.

Write `review/result.yaml` conforming to `contracts/review-result.schema.json`. Each finding needs id, severity, category, exact file/location, observed behavior, concrete risk, actionable recommendation, confidence, and blocking status. Do not pad the report with style preferences or claims unsupported by code.

Critical and high findings block the gate. Every medium finding must be fixed, accepted, or deferred with a reason. If no findings exist, identify the reviewed scope and residual limitations; absence of findings is not proof that unexecuted runtime behavior works.
