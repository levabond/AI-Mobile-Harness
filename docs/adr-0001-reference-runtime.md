# ADR-0001: Reference runtime and primary platform

## Decision

Use a Python 3.9 standard-library CLI as the thin gate/evidence runtime and SwiftUI/iOS as the primary mobile stack. Adopt Superpowers for R&D and verification, and MobileBuildMCP for Apple build/test/device execution. Store `.yaml` documents in the JSON-compatible YAML 1.2 subset so the harness itself needs no parser dependency.

## Consequences

- The CLI runs without package downloads.
- Configuration remains valid YAML, though generated files use JSON formatting.
- Engineering method stays in versioned methodology contracts rather than being hidden inside local skills.
- Platform-specific behavior stays in MobileBuildMCP and adapter routing.
- The MVP fixture is a Swift Package containing a SwiftUI screen and XCTest contract tests. Simulator UI automation remains an explicit unsupported capability for that fixture.
