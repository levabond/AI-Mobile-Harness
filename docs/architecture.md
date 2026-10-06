# Architecture

`mobile_harness` is a standard-library-only gate and evidence engine. It loads JSON-compatible YAML, selects declarative workflows and profiles, stores immutable command evidence, and derives decisions. It does not try to encode engineering judgment in Python.

Superpowers supplies the normative R&D and verification method. Workflow metadata names the exact upstream process, and artifacts record classification, approval, fresh verification, and failure routing. MobileBuildMCP supplies Apple execution. Agents use its MCP server; deterministic gates use its CLI, which shares the same tool implementations.

Stable context lives in `.mobile-harness/context/`. Per-work-item state and evidence live in `.mobile-harness/runs/<id>/` and are normally local CI artifacts. Codex skills specialize the methodology for mobile discovery, planning, implementation, review, and QA; they do not define a competing process.

The first adapter targets iOS projects. Real Xcode projects and Swift packages default to MobileBuildMCP. The reproducible fixture explicitly selects a native Swift fallback so offline CI can validate SwiftUI source and behavior without pretending that it performed simulator UI automation.
