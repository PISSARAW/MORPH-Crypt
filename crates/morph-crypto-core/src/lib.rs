//! Standalone cryptographic core.
//!
//! No construction is implemented yet. Add only reviewed, standard
//! cryptographic building blocks here; experimental morphology belongs in
//! policy and transition crates, not in ad-hoc primitive implementations.

/// Indicates that this crate is scaffolding and has no usable cipher API.
pub const IMPLEMENTATION_STATUS: &str = "scaffold-only";
