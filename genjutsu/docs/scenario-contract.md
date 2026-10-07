# Scenario contract v1

A scenario is a portable description of one controlled application reality.
The v1 executable adapter consumes `network`; future mobile adapters can consume
the other sections without changing the scenario identity.

## Root fields

| Field | Required | Description |
|---|---:|---|
| `version` | yes | Contract version; currently `1` |
| `name` | yes | Stable scenario identifier |
| `description` | no | Human-readable intent |
| `network` | no | HTTP routes and fallback behavior |
| `device` | no | Connectivity, locale, permissions, battery, and device state |
| `storage` | no | Local database, cache, preferences, and keychain state |
| `time` | no | Fixed time, timezone, and clock behavior |
| `identity` | no | User, role, subscription, and authentication state |
| `events` | no | Push, deep link, lifecycle, and external events |
| `expected` | no | Expected screens, events, and other scenario outcomes |

Unknown fields are retained so adapters can evolve independently. A later strict
validation mode may optionally reject unknown fields.

## Network

```json
{
  "network": {
    "routes": [],
    "default": {
      "status": 404,
      "body": { "error": "not_found" }
    }
  }
}
```

`routes` is an ordered list, although duplicate method/path pairs are rejected in
v1. `default` is used when no route matches.

## Route

```json
{
  "method": "GET",
  "path": "/profile",
  "response": {
    "status": 200,
    "delay_ms": 250,
    "headers": {
      "Cache-Control": "no-store"
    },
    "body": {
      "id": "user-1",
      "name": "Demo User"
    }
  }
}
```

### Matching rules in v1

- Method comparison is case-insensitive.
- Path comparison is exact and case-sensitive.
- Query strings are recorded but do not affect matching.
- Request headers and bodies do not affect matching.
- Only one route may exist for a method/path pair.

These constraints keep early scenarios deterministic. Predicate matching and
stateful sequences belong to a later contract version.

## Response

| Field | Default | Constraints |
|---|---:|---|
| `status` | `200` | Integer from 100 through 599 |
| `delay_ms` | `0` | Non-negative number |
| `headers` | `{}` | String-to-string map |
| `body` | `null` | JSON value or text |

Object and array bodies are encoded as JSON. All other bodies are encoded as
plain UTF-8 text unless `Content-Type` is explicitly supplied.

## Evolution rules

- A scenario must declare its contract version.
- Breaking changes require a new version.
- Adapters must publish supported capabilities.
- Unsupported sections must be reported, never silently claimed as executed.
- Recorded scenarios should be sanitized before they are committed.
