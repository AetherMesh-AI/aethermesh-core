# 0001: First Core Module Seam

## Status

Accepted.

## Decision

The first implementation target is a small TypeScript module running on the active Node.js LTS line. This choice applies only to the first core validation module; it does not require every future AetherMesh component to use TypeScript or Node.js.

The first module will validate and normalize data only. It will not open sockets, connect to peers, discover peers, persist configuration, run a daemon, or manage cryptographic key material.

## Mesh Node Identity Contract

A mesh node identity input must include:

- `node_id`: stable identifier. Required string, 3-64 characters, lowercase ASCII letters, digits, and hyphens only. It must start with a letter and end with a letter or digit.
- `public_key_id`: stable key-material reference. Required string, 8-128 characters. It names key material managed elsewhere and must not contain private key material.

A mesh node identity input may include:

- `display_name`: display metadata only. Optional string, 1-80 characters after trimming. It is never a stable identifier.

Valid identity example:

```json
{
  "node_id": "alpha-node-1",
  "public_key_id": "ed25519:alpha-node-1:2026-06",
  "display_name": "Alpha Node 1"
}
```

Invalid identity examples that validation must reject later:

- `{ "node_id": "Alpha Node 1", "public_key_id": "ed25519:alpha-node-1:2026-06" }` because `node_id` contains uppercase letters and spaces.
- `{ "node_id": "ab", "public_key_id": "short" }` because `node_id` and `public_key_id` are too short.

## Peer Endpoint Contract

A peer endpoint input must include:

- `node_id`: stable identifier for the peer node using the same rules as mesh node identity `node_id`.
- `endpoint_uri`: required URI string, 1-256 characters, with a lowercase scheme, host, and optional port. The first module only parses, validates, and normalizes this value; it does not imply any networking behavior.

A peer endpoint input may include:

- `label`: display metadata only. Optional string, 1-80 characters after trimming.

Valid endpoint example:

```json
{
  "node_id": "alpha-node-1",
  "endpoint_uri": "tcp://alpha-node-1.local:4739",
  "label": "LAN endpoint"
}
```

Invalid endpoint examples that validation must reject later:

- `{ "node_id": "alpha-node-1", "endpoint_uri": "alpha-node-1.local:4739" }` because the endpoint URI has no scheme.
- `{ "node_id": "Alpha Node 1", "endpoint_uri": "tcp://:4739" }` because the node id is invalid and the URI has no host.

## Validation Result Style

Validation must be deterministic and side-effect-free. Given the same input, validation must return the same result without reading files, using clocks, generating random values, opening sockets, or mutating external state.

A validation success returns:

- `ok: true`
- `value`: normalized identity or endpoint value using the contract fields above

A validation failure returns:

- `ok: false`
- `errors`: one or more stable errors, each with a stable `code`, human-readable `message`, and optional `field`

Error codes must be stable enough for tests and consumers to assert against. Error messages may improve over time but should remain deterministic for the same failure.

## Non-goals

This decision does not add or design:

- Networking or transport behavior.
- Peer discovery.
- Persistence or configuration files.
- Daemon, service, CLI, UI, or deployment lifecycle.
- Cryptographic key management beyond naming `public_key_id` as an external key-material reference.
- Package scaffolding, CI, and tests; those wait for the follow-up implementation PR.
