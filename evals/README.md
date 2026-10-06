# Evaluations

Run the first end-to-end evaluation with:

```bash
python3 -m mobile_harness eval profile-details
```

The runner copies the fixture to an isolated temporary directory, performs discovery and the complete standard feature workflow, executes Swift build/lint/tests, validates artifacts, and derives the final decision. The malformed fixture is a negative discovery case.

