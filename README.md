# MORPH-Crypt

MORPH-Crypt is an independent research project for studying morphogenetic
cryptographic systems. GenOS coordinates research and records evidence; the
cryptographic runtime is designed to build and operate without GenOS.

> **Research status:** the core contains an experimental AEAD wrapper. Key
> generation, persistence, rotation and recovery are not implemented. Do not
> use it to protect real data.

## Workspace

- `crates/morph-crypto-core` — standalone cryptographic primitives and APIs.
- `crates/morph-crypto-policy` — versioned morphology and transition policies.
- `crates/morph-crypto-lineage` — key lineage and lifecycle metadata.
- `crates/morph-crypto-transition` — explicit, auditable state transitions.
- `crates/morph-crypto-verifier` — independent checks for declared invariants.
- `genos/` — pinned integration contract and project registration metadata.
- `research/` — hypotheses, candidate constructions, threat models and sources.
- `formal/` — formal models; a directory is not evidence that a property is proved.
- `benchmarks/` — reproducible baselines and adversarial experiments.
- `evidence/` — qualification records and experiment receipts.

## Build

Requires Rust 1.88 or newer.

```sh
cargo build --workspace --locked
```

Commits follow the [GenOS contribution and commit rules](CONTRIBUTING.md).
Install the repository hooks with:

```sh
git config core.hooksPath .githooks
```

See [the initial threat model](research/threat-models/initial.md) before
proposing a construction.
