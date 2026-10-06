# Security policy

Please report vulnerabilities privately to the repository maintainers rather than opening a public issue.

The harness executes only adapter commands declared by repository configuration. Review configuration changes before running them. Command output is redacted for common secret formats before it is written to evidence. Network, publish, release, destructive, dependency, privacy, and migration actions require explicit human approval.

The MobileBuildMCP package is version-pinned and its Sentry telemetry is disabled in the checked-in Codex MCP configuration. Updating the pin is a dependency change and requires review.
