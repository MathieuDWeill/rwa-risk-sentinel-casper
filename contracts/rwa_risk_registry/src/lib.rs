#![cfg_attr(not(test), no_std)]
#![cfg_attr(not(test), no_main)]

//! RWA Risk Registry — Odra-style Casper smart contract starter.
//!
//! Stores compact, verifiable RWA risk attestations on-chain while keeping bulky
//! evidence off-chain as JSON/IPFS/API data referenced by a cryptographic hash.

extern crate alloc;

use odra::prelude::*;

#[odra::odra_type]
pub struct RiskAttestation {
    pub asset_id: String,
    pub score_bps: u32,
    pub confidence_bps: u32,
    pub evidence_hash: String,
    pub summary: String,
    pub timestamp_ms: u64,
    pub publisher: Address,
}

#[odra::module]
pub struct RwaRiskRegistry {
    owner: Var<Address>,
    latest_by_asset: Mapping<String, RiskAttestation>,
    publisher_count: Mapping<Address, u64>,
    asset_count: Var<u64>,
}

#[odra::module]
impl RwaRiskRegistry {
    pub fn init(&mut self) {
        self.owner.set(self.env().caller());
        self.asset_count.set(0);
    }

    pub fn publish_attestation(
        &mut self,
        asset_id: String,
        score_bps: u32,
        confidence_bps: u32,
        evidence_hash: String,
        summary: String,
        timestamp_ms: u64,
    ) {
        assert!(score_bps <= 10_000, "score_bps must be <= 10000");
        assert!(confidence_bps <= 10_000, "confidence_bps must be <= 10000");
        assert!(!asset_id.is_empty(), "asset_id required");
        assert!(!evidence_hash.is_empty(), "evidence_hash required");
        assert!(summary.len() <= 280, "summary too long");

        let caller = self.env().caller();
        let previous = self.latest_by_asset.get(&asset_id);
        if previous.is_none() {
            self.asset_count.set(self.asset_count.get_or_default() + 1);
        }

        let attestation = RiskAttestation {
            asset_id: asset_id.clone(),
            score_bps,
            confidence_bps,
            evidence_hash,
            summary,
            timestamp_ms,
            publisher: caller,
        };

        self.latest_by_asset.set(&asset_id, attestation);
        let count = self.publisher_count.get(&caller).unwrap_or(0);
        self.publisher_count.set(&caller, count + 1);
    }

    pub fn latest(&self, asset_id: String) -> Option<RiskAttestation> {
        self.latest_by_asset.get(&asset_id)
    }

    pub fn publisher_reputation(&self, publisher: Address) -> u64 {
        self.publisher_count.get(&publisher).unwrap_or(0)
    }

    pub fn total_assets(&self) -> u64 {
        self.asset_count.get_or_default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use odra::host::{Deployer, NoArgs};
    use odra_test::env;

    #[test]
    fn publishes_latest_attestation() {
        let test_env = env();
        let mut contract = RwaRiskRegistry::deploy(&test_env, NoArgs);

        contract.publish_attestation(
            "invoice-2026-001".to_string(),
            2700,
            8400,
            "sha256:abc".to_string(),
            "Payment current; macro risk elevated".to_string(),
            1_782_345_600_000,
        );

        let latest = contract.latest("invoice-2026-001".to_string()).unwrap();
        assert_eq!(latest.score_bps, 2700);
        assert_eq!(contract.total_assets(), 1);
    }
}
