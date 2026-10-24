# Initial threat model

Status: starting assumptions for research, not a validated security model.

## Assets

- Plaintext and derived secret keys.
- Key lineage, policy versions, and transition authorization.
- Ciphertext integrity and the ability to decrypt data after an approved
  transition.

## Adversary

Assume an attacker can observe, replay, reorder, modify, truncate, and inject
messages; can cause process interruption during a transition; and may know
public policies and implementation details. GenOS, its workers, logs, and
experiment artifacts are outside the cryptographic trusted computing base.

## Initial security goals

- Confidentiality and authenticity must come from established, reviewed
  cryptographic constructions rather than a novel cipher assembled here.
- State transitions must be explicit, authorized, versioned, and fail closed.
- A failed or interrupted transition must not silently lose the only usable
  key or accept a partially installed policy.
- Secret key material must not enter logs, snapshots, benchmarks, or evidence.
- The runtime must remain operable when GenOS is unavailable.

## Out of scope until specified

Side-channel resistance, post-quantum security, forward secrecy, secure
deletion, rollback resistance across hostile storage, distributed consensus,
and production key custody. Each requires a separate model and evidence.

## Open questions

1. What data and deployment model is the first construction intended to protect?
2. Which standard AEAD and key derivation APIs will provide the fixed primitive
   layer?
3. What attacker capabilities and compromise recovery goals are required for
   morphology and key transitions?

No production-use claim is justified until these questions and independent
cryptographic review are addressed.
