# Testnet Transactions & Deployment Guide

This document tracks the smart contract deployment hash and the RWA risk attestation transaction hashes on Casper Testnet.

## How to Deploy and Generate Hashes

To produce real Casper Testnet transactions:

1. **Get a Funded Account**:
   - If you don't have a Casper keypair, run `./scripts/deploy_contract_placeholder.sh` once. It will generate a new keypair in the `keys/` directory.
   - Print your public key: `cat keys/public_key_hex` (e.g. `01230b71b1bcb9486318c9e74fe4655c82258badf61cf45528887b3daf50de4c3c`).
   - Go to [Casper Testnet Faucet](https://testnet.cspr.live/tools/faucet), connect your wallet or request tokens for this public key address.
   
2. **Deploy the Smart Contract**:
   - Run the deploy script:
     ```bash
     ./scripts/deploy_contract_placeholder.sh keys/secret_key.pem
     ```
   - This compiles the contract with the correct Rust toolchain, deploys it to Casper Testnet, waits for execution, retrieves the contract hash, and automatically writes it to `agent/.env` (setting `AGENT_MODE=real`).

3. **Submit Attestations via the Agent**:
   - Start the FastAPI agent: `make agent` (runs on port 8080).
   - Trigger the demo cycle to send 3 real RWA attestation transactions:
     ```bash
     AGENT_MODE=real python scripts/run_demo_cycle.py --asset invoice-2026-001 --count 3 --real
     ```
   - The CLI and dashboard will display the real Casper deploy hashes!

## Casper Testnet Explorer Logs

Once you run the steps above, record the hashes below for your DoraHacks submission page:

| Purpose | Deploy Hash | Explorer Link | Notes |
|---|---|---|---|
| Contract Deploy | `[Your Contract Deploy Hash]` | `https://testnet.cspr.live/deploy/[Hash]` | RWA Risk Registry |
| Attestation 1 | `[Your Attestation Hash 1]` | `https://testnet.cspr.live/deploy/[Hash]` | `invoice-2026-001` |
| Attestation 2 | `[Your Attestation Hash 2]` | `https://testnet.cspr.live/deploy/[Hash]` | `carbon-credit-kenya-042` |
| Attestation 3 | `[Your Attestation Hash 3]` | `https://testnet.cspr.live/deploy/[Hash]` | `real-estate-note-nyc-17` |
