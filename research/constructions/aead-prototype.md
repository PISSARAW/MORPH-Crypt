# AEAD prototype: XChaCha20-Poly1305

Status: experimental implementation scaffold; not production-qualified.

The `morph-crypto-core` crate delegates authenticated encryption to
RustCrypto's pinned `chacha20poly1305` 0.11.0 dependency. It uses XChaCha20-
Poly1305 and obtains a fresh 24-byte nonce from the OS CSPRNG for each `seal`
call. The serialized envelope is `nonce || ciphertext || authentication tag`.
Associated data is authenticated but remains external to the envelope and
must be supplied unchanged to `open`.

The 24-byte nonce variant is selected for this prototype so callers do not
manage a short counter nonce. This does not establish safe key generation,
key storage, process-fork behavior, rollback resistance, side-channel
resistance, or suitability for any deployment. A random nonce is not a
substitute for a key lifecycle protocol. The crate accepts key bytes from an
external key-management layer and does not generate or persist keys.

The prototype has not been independently reviewed or formally verified.
Before any use beyond research, define per-key usage limits, define the wire
format and versioning policy, add adversarial and known-answer tests, review
memory handling and platform RNG behavior, and obtain independent cryptographic
review.

Reference implementation documentation: [RustCrypto chacha20poly1305 0.11.0](https://docs.rs/chacha20poly1305/0.11.0/chacha20poly1305/).
