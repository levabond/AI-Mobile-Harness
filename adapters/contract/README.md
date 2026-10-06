# Adapter contract

An adapter detects a project and resolves abstract operations to provider-tagged argument arrays. Required discovery output is a project profile conforming to `contracts/project-profile.schema.json`.

Operations are `detect_project`, `describe_project`, `resolve_targets`, `build_app`, `build_tests`, `run_unit_tests`, `run_integration_tests`, `run_ui_tests`, `run_lint`, `run_format_check`, `launch_device`, `install_app`, `open_route`, `capture_screenshot`, `collect_logs`, `list_localizations`, `inspect_accessibility`, and `clean_generated_artifacts`.

An implementation must return `unsupported` rather than inventing evidence. Commands are arrays and execute without a shell. Output must be redacted before persistence. The iOS adapter uses MobileBuildMCP by default; raw Apple commands are allowed only for an explicit hermetic fallback.
