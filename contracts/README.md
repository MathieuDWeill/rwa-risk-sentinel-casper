# RWA Risk Registry Smart Contract

This folder contains the Casper smart contract written using the **Odra Smart Contract Framework (v1.5.1)**. It provides a decentralized registry for Real World Asset (RWA) risk assessments, storing compact risk score details and evidence hashes on-chain while keeping private details off-chain.

## Prerequisites

Ensure you have Rust, cargo, and the wasm targets installed. If not, follow these steps:

```bash
# Install rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# Install target wasm32-unknown-unknown
rustup target add wasm32-unknown-unknown

# Install cargo-odra CLI tool (compatible with Odra v1)
cargo install cargo-odra --locked
```

*Note: Since Odra v1 macros rely on specific compiler features, this contract must be compiled using an older nightly toolchain (e.g. `nightly-2024-09-05`).*

```bash
rustup toolchain install nightly-2024-09-05
rustup target add wasm32-unknown-unknown --toolchain nightly-2024-09-05
```

## Compilation

To compile the contract to WebAssembly for Casper deployment:

```bash
cd contracts/rwa_risk_registry
cargo +nightly-2024-09-05 odra build
```

This compiles the contract and saves the optimized bytecode to:
`contracts/rwa_risk_registry/wasm/RwaRiskRegistry.wasm`

## Running Tests

To run the unit tests against the local simulated OdraVM:

```bash
cd contracts/rwa_risk_registry
cargo odra test
```

## Deployment to Casper Testnet

You can use the deployment script in the root of the repository to compile and deploy:

```bash
./scripts/deploy_contract_placeholder.sh [PATH_TO_SECRET_KEY_PEM]
```

Or deploy manually via the Casper client CLI:

```bash
casper-client put-transaction session \
  --wasm-path contracts/rwa_risk_registry/wasm/RwaRiskRegistry.wasm \
  --chain-name casper-test \
  --gas-price-tolerance 1 \
  --secret-key keys/secret_key.pem \
  --payment-amount 50000000000 \
  --standard-payment true \
  --session-arg "odra_cfg_package_hash_key_name:string='rwa_risk_registry'" \
  --session-arg "odra_cfg_allow_key_override:bool='true'" \
  --session-arg "odra_cfg_is_upgradable:bool='false'" \
  --node-address https://node.testnet.casper.network/rpc
```
