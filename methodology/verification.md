# Verification method

Normative upstream processes:

- `superpowers:verification-before-completion` for every success claim;
- `superpowers:systematic-debugging` after a build, test, or runtime failure.

For every required claim, identify its proving command or observable artifact, execute it fresh, read the complete result and exit code, and link the evidence. Previous runs, source inspection, and statements such as “should pass” are not evidence.

Apple build and test commands are routed through MobileBuildMCP. Its MCP tools are preferred for interactive agent work; its CLI uses the same tool implementations and is used by the deterministic harness runner. Raw `xcodebuild` is not the default backend.

When a check fails, verification stops with the actual result. A repair loop may begin only by following systematic debugging: reproduce, gather evidence, compare working examples, form one hypothesis, test minimally, then make one root-cause fix. Three failed fixes require architectural reconsideration and human discussion.

