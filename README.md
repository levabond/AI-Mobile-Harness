# Mobile Engineering Harness

An evidence-driven mobile development methodology with executable gates.

The methodology is the product. Skills are thin entry points; the CLI records artifacts and enforces gates.

- [Superpowers](https://github.com/obra/superpowers) governs R&D and verification.
- [MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP) performs Apple builds, tests, simulator/device operations, logs, and UI automation.
- Mobile Engineering Harness adds project discovery, mobile contracts, risk profiles, scope discipline, review, QA, and a derived final decision.

A required check is `passed` only when the harness has fresh command evidence, its exit code, provider, and redacted log.

## MVP scope

This repository deliberately implements one small vertical slice:

- one primary stack: SwiftUI/iOS, with a Swift Package fixture;
- one demo feature: Profile Details;
- one linear feature workflow;
- one standard-library-only Python gate/evidence CLI;
- Superpowers-backed R&D and verification;
- MobileBuildMCP as the default build/test backend for real projects;
- thin mobile-specific skills;
- build, swift-format, XCTest, review, QA, and final-report artifacts.

It does not include a second platform, automatic repair loops, a dashboard, release automation, multi-agent orchestration, or a general YAML parser. `.yaml` files use the JSON-compatible YAML 1.2 subset so the CLI works on Python 3.9 without downloads.

## Try the vertical slice

Requirements: macOS with Xcode/Swift 6, Python 3.9+, and the Superpowers Codex plugin. Real project builds additionally use MobileBuildMCP through the checked-in Codex MCP configuration. `npx` requires Node.js 18+; a Homebrew/global `mobilebuildmcp` installation can be configured instead.

Install Superpowers from the Codex plugin marketplace (`/plugins`, search for `superpowers`). The repository already contains `.codex/config.toml` for MobileBuildMCP 2.7.1.

```bash
python3 -m mobile_harness doctor
python3 -m mobile_harness eval profile-details
```

The eval copies `evals/fixtures/ios-small-clean` to a temporary directory, runs the full workflow, and returns `ready_with_accepted_risk`. For hermetic CI it explicitly uses native Swift commands instead of downloading MobileBuildMCP. Production `init` configuration enables MobileBuildMCP by default. The accepted risk is explicit: the fixture does not launch an iOS Simulator or claim XCUITest evidence.

Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

## Use it on a Swift project

From this checkout:

```bash
python3 -m pip install -e .
mobile-harness --project /path/to/project init --platform ios
mobile-harness --project /path/to/project discover project
mobile-harness --project /path/to/project start feature "Profile Details" --spec examples/profile-details-request.yaml
mobile-harness --project /path/to/project run feature
mobile-harness --project /path/to/project status
```

For an actual product feature, Codex runs Superpowers brainstorming first and records its classification and approval. Build/test operations resolve to MobileBuildMCP. Verification then follows Superpowers verification-before-completion; failures route to systematic debugging. Local skills only add mobile-specific context and artifact contracts.

## Output

Stable project context is written to `.mobile-harness/context/`. A work item is stored under:

```text
.mobile-harness/runs/<work-item-id>/
├── manifest.yaml
├── rnd/
├── plan/
├── dev/
├── verification/
├── review/
├── qa/
├── evidence/
├── final-report.yaml
└── final-report.md
```

Run evidence is intended for local or CI artifact retention and is ignored by Git. Start with the [methodology](methodology/README.md), then see [architecture](docs/architecture.md), [lifecycle](methodology/lifecycle.md), and [adapter contract](adapters/contract/README.md).
