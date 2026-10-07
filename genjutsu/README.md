# Genjutsu

Genjutsu is a controlled-reality engine for mobile development and testing.
It places a deterministic simulation layer between an application and the
external world, so rare states, failures, and edge cases can be reproduced on
demand.

> The app believes the environment is real. You control the reality.

This repository contains an early executable MVP. It currently focuses on HTTP
simulation and the lifecycle of an active scenario. Device state, storage,
time, push notifications, deep links, recording, and native mobile SDKs are
described by the scenario contract and planned as adapters.

## Why it exists

Traditional mocks usually live inside individual tests. Genjutsu treats the
whole environment as one reusable scenario that can be shared by development,
automated verification, QA, demos, and bug reproduction.

A scenario can describe:

- API responses, errors, and latency;
- device and connectivity state;
- local storage and user identity;
- expected screen and analytics events;
- the conditions needed to reproduce a defect.

Only HTTP behavior is executed by this MVP. The remaining sections are retained
in the scenario so future mobile adapters can consume the same contract.

## Quick start

The MVP requires Python 3.9+ and has no runtime dependencies.

```bash
cd genjutsu

# Validate a scenario
PYTHONPATH=src python3 -m genjutsu validate examples/expired-session.json

# Activate a controlled reality
PYTHONPATH=src python3 -m genjutsu cast examples/expired-session.json

# Inspect the active reality
PYTHONPATH=src python3 -m genjutsu inspect

# Start the mock HTTP server
PYTHONPATH=src python3 -m genjutsu serve --port 8787

# Return to the real environment
PYTHONPATH=src python3 -m genjutsu release
```

Or cast and serve in one command:

```bash
PYTHONPATH=src python3 -m genjutsu run examples/slow-profile.json --port 8787
```

After an editable install, the shorter command is available:

```bash
python3 -m pip install -e .
genjutsu run examples/expired-session.json
```

## CLI language

```text
genjutsu validate <scenario>  Validate a scenario contract
genjutsu cast <scenario>      Activate a controlled reality
genjutsu inspect              Show the active reality
genjutsu serve                Serve the active HTTP simulation
genjutsu run <scenario>       Cast and serve a scenario
genjutsu release              Return to the real environment
```

The thematic language is intentionally limited to the product surface. Internal
contracts use conventional engineering terms such as scenario, route, response,
adapter, and evidence.

## Scenario example

```json
{
  "version": 1,
  "name": "expired-session",
  "description": "The user opens Profile with an expired session.",
  "network": {
    "routes": [
      {
        "method": "GET",
        "path": "/profile",
        "response": {
          "status": 401,
          "delay_ms": 300,
          "body": { "error": "session_expired" }
        }
      }
    ]
  },
  "device": {
    "network": "wifi",
    "locale": "en-US"
  },
  "storage": {
    "auth_token": "expired"
  },
  "expected": {
    "screen": "login",
    "events": ["session_expired"]
  }
}
```

The full contract is documented in
[`docs/scenario-contract.md`](docs/scenario-contract.md).

## Request behavior

The server performs exact matching by HTTP method and URL path. Query strings do
not participate in matching in the MVP. If no route matches, `network.default`
is used. Without a configured default response, the server returns a diagnostic
`404`.

Every response includes:

```text
X-Genjutsu-Scenario: <scenario-name>
```

Requests are recorded as JSON Lines in `.genjutsu/requests.jsonl` by default.
The active reality is stored in `.genjutsu/active.json`. Override the latter
with `--state-file` or the `GENJUTSU_STATE_FILE` environment variable.

## Tests

```bash
cd genjutsu
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Architecture

```text
Scenario file
     ↓ validate
Scenario contract
     ↓ cast
Active reality state
     ↓
HTTP adapter → mobile application
     ↓
Request evidence log
```

Planned adapter boundary:

```text
Genjutsu Core
├── Network adapter
├── Device adapter
├── Storage adapter
├── Time adapter
├── Identity adapter
└── Event adapter
```

## Roadmap

### MVP 0.1

- [x] Scenario validation
- [x] Active scenario lifecycle
- [x] HTTP route simulation
- [x] Response latency and failure statuses
- [x] Request evidence log
- [x] Example scenarios
- [x] Standard-library test suite

### Next

- [ ] YAML scenario support
- [ ] Record and replay proxy
- [ ] Scenario composition and inheritance
- [ ] Request body, header, and query matching
- [ ] Runtime scenario switching
- [ ] Assertions over captured requests
- [ ] iOS adapter and developer menu
- [ ] Android adapter and developer menu
- [ ] Device, storage, time, and event adapters
- [ ] Integration with Mobile Engineering Harness
- [ ] CI reports and scenario catalog UI

## Naming note

Before a public commercial launch, perform a dedicated trademark and package-name
availability review. The implementation keeps its technical contracts generic
so the project can be renamed without redesigning its architecture.
