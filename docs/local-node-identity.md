# Local Node Identity Format

AetherMesh Phase 1 uses a small public identity document for one local prototype node. The document is local-first and audit-oriented: it gives manifests, validation receipts, lineage records, and contribution logs a stable node reference without requiring public networking, registry lookup, token state, or dashboard state.

## Version 1 document shape

A version 1 public local node identity is a JSON object with these fields:

- `node_id`: stable local node identifier. It is generated locally, non-secret, and safe to copy into manifests, validation receipts, lineage records, and contribution logs.
- `creator_node_id`: the node that created this identity or produced derived work. Keep this separate from generated work IDs, receipt IDs, lineage IDs, job IDs, and contribution record IDs.
- `created_at`: ISO 8601 timestamp with a timezone.
- `identity_version`: integer identity format version. The current value is `1`.
- `public_key`: public signing/verification key reference for local prototype attribution. This is public material only.
- `manifest_ref`: local manifest linkage such as `examples/local-batch.json#node:<node_id>`. It is a local file or fixture reference, not a network registry, token state, or dashboard lookup.
- `local_metadata` (optional): inspectable local-only metadata for development notes such as display name or fixture environment. It must not be required for validation.

## Private key material

Private key material is stored outside the public identity document in the local node home, for example under `~/.aethermesh/keys/` or the directory selected by `AETHERMESH_HOME`. Private keys, secret keys, seeds, mnemonics, and passwords must never be copied into manifests, validation receipts, lineage records, contribution records, or the public identity document.

The public identity may include only `public_key`. Portable records should reference `node_id`, `creator_node_id`, `manifest_ref`, and public validation data.

## Manifest linkage

`manifest_ref` links identity to a local node manifest by path or fixture fragment. It does not imply peer discovery, networking, a public registry, token balances, rewards, or dashboard state. A local runner can resolve the reference by loading the file in the current repository or configured local home.

## Minimal example

See `examples/local-node-identity.json`:

```json
{
  "node_id": "node-local-7f3a9c2e",
  "creator_node_id": "node-local-7f3a9c2e",
  "created_at": "2026-07-08T00:00:00Z",
  "identity_version": 1,
  "public_key": "ed25519-pub-local-example-7f3a9c2e",
  "manifest_ref": "examples/local-batch.json#node:node-local-7f3a9c2e",
  "local_metadata": {
    "display_name": "Local prototype node",
    "environment": "dev-fixture"
  }
}
```

## Versioning rules

- Increment `identity_version` whenever required fields, field meanings, or validation rules change.
- Additive optional fields may remain version 1 only when old validators can ignore them safely.
- New versions should preserve `node_id`, `creator_node_id`, `created_at`, `public_key`, and `manifest_ref` where possible so old receipts and contribution records remain attributable.
- Migrations must be explicit and should keep older version 1 documents parseable unless a security issue requires rejection.
- Do not expand identity into registry, rewards, networking, or dashboard concerns; those belong to later protocol layers.
