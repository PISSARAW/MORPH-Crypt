//! Explicit transitions between versioned cryptographic states.
//!
//! Transitions must be atomic from the caller's perspective and must fail
//! closed if a candidate state cannot be verified.

/// Indicates that no transition protocol is implemented yet.
pub const IMPLEMENTATION_STATUS: &str = "specification-pending";
