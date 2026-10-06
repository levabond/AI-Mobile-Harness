# Mobile Engineering Harness methodology

The methodology is the product. Skills are thin entry points and the CLI is a gate/evidence engine; neither defines the process by itself.

The MVP composes two upstream systems:

1. **Superpowers** governs R&D and verification. R&D uses `superpowers:brainstorming`: classify the work as spike, bounded, or architectural; inspect project context; make design and trade-offs explicit; obtain approval before implementation. Verification uses `superpowers:verification-before-completion`: identify the command that proves each claim, run it fresh, read the result, and only then record a pass. A failure transitions to `superpowers:systematic-debugging`, never guess-and-patch.
2. **MobileBuildMCP** owns Apple build, test, simulator, device, log, and UI-automation operations. The project-scoped MCP server is the agent interface. The same package's CLI is the deterministic adapter interface used to capture exit codes and logs.

The harness adds mobile-specific artifacts, risk profiles, scope controls, QA, review, and the final gate around those upstream methods. It does not copy or fork upstream skills.

```text
Intent
  -> Superpowers brainstorming / approval
  -> project-native plan and implementation
  -> MobileBuildMCP build and test evidence
  -> Superpowers verification-before-completion
  -> review + mobile QA
  -> derived final decision
```

See [R&D](rnd.md), [verification](verification.md), and the integration contracts in `integrations/`.

