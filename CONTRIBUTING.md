# Contributing

Use Python 3.9+ and Swift 6+ for the reference fixture.

Before opening a change, run:

```bash
python3 -m unittest discover -s tests -v
python3 -m mobile_harness doctor
python3 -m mobile_harness eval profile-details
```

New adapters must implement `adapters/contract/adapter.schema.json`, report unsupported capabilities explicitly, and include contract tests. New skills need a discriminating trigger description, a negative boundary, and validation with the bundled skill validator.

