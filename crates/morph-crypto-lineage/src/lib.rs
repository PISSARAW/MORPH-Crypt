//! Key lifecycle and lineage metadata, kept distinct from key material.
//!
//! Secret values must never be placed in lineage records, logs, or evidence.

/// Indicates that no key lifecycle is implemented yet.
pub const IMPLEMENTATION_STATUS: &str = "specification-pending";
