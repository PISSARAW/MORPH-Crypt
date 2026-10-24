//! Standalone cryptographic core.
//!
//! Experimental AEAD wrapper using RustCrypto XChaCha20-Poly1305.
//!
//! This is a research prototype, not a production-ready key management system.
//! The cryptographic implementation is delegated to the pinned RustCrypto
//! dependency; no cipher or authenticator is implemented in this crate.

use chacha20poly1305::aead::{Aead, Generate, KeyInit, Payload};
use chacha20poly1305::{XChaCha20Poly1305, XNonce};
use zeroize::Zeroize;

const NONCE_LENGTH: usize = 24;
const TAG_LENGTH: usize = 16;

/// Errors returned by the prototype AEAD interface.
#[derive(Debug, PartialEq, Eq)]
pub enum CryptoError {
    /// The operating system cryptographic random number generator failed.
    RandomnessUnavailable,
    /// The encrypted envelope is too short to contain nonce and tag.
    MalformedEnvelope,
    /// Encryption could not produce a ciphertext.
    EncryptionFailed,
    /// Authentication failed or the ciphertext was modified.
    AuthenticationFailed,
}

/// Secret key wrapper that clears its stored bytes when dropped.
pub struct SecretKey([u8; 32]);

impl SecretKey {
    /// Construct from exactly 32 bytes supplied by a key-management layer.
    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }
}

impl Drop for SecretKey {
    fn drop(&mut self) {
        self.0.zeroize();
    }
}

/// A small, standalone XChaCha20-Poly1305 research interface.
pub struct AeadBox {
    cipher: XChaCha20Poly1305,
}

impl AeadBox {
    /// Initialize the primitive from a 256-bit key.
    pub fn new(key: &SecretKey) -> Self {
        Self {
            cipher: XChaCha20Poly1305::new_from_slice(&key.0)
                .expect("fixed-size key always has the required length"),
        }
    }

    /// Encrypt and authenticate a message, prefixing a fresh random nonce.
    ///
    /// The returned envelope is `nonce || ciphertext || tag` and does not
    /// contain the associated data; callers must supply the same data to open.
    pub fn seal(&self, plaintext: &[u8], associated_data: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let nonce = XNonce::try_generate().map_err(|_| CryptoError::RandomnessUnavailable)?;
        let encrypted = self
            .cipher
            .encrypt(
                &nonce,
                Payload {
                    msg: plaintext,
                    aad: associated_data,
                },
            )
            .map_err(|_| CryptoError::EncryptionFailed)?;
        let mut envelope = Vec::with_capacity(NONCE_LENGTH + encrypted.len());
        envelope.extend_from_slice(nonce.as_slice());
        envelope.extend_from_slice(&encrypted);
        Ok(envelope)
    }

    /// Authenticate and decrypt an envelope produced by [`Self::seal`].
    pub fn open(&self, envelope: &[u8], associated_data: &[u8]) -> Result<Vec<u8>, CryptoError> {
        if envelope.len() < NONCE_LENGTH + TAG_LENGTH {
            return Err(CryptoError::MalformedEnvelope);
        }
        let (nonce_bytes, encrypted) = envelope.split_at(NONCE_LENGTH);
        let nonce = XNonce::try_from(nonce_bytes).map_err(|_| CryptoError::MalformedEnvelope)?;
        self.cipher
            .decrypt(
                &nonce,
                Payload {
                    msg: encrypted,
                    aad: associated_data,
                },
            )
            .map_err(|_| CryptoError::AuthenticationFailed)
    }
}
