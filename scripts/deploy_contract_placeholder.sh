#!/usr/bin/env bash
set -euo pipefail

# Configuration
SECRET_KEY="${1:-keys/secret_key.pem}"
NODE_ADDRESS="${2:-https://node.testnet.casper.network/rpc}"
CHAIN_NAME="${3:-casper-test}"
PAYMENT_AMOUNT=50000000000 # 50 CSPR

# Check keys exist
if [ ! -f "$SECRET_KEY" ]; then
    echo "ERROR: Secret key not found at $SECRET_KEY"
    echo "Generating keypair in keys/ directory..."
    mkdir -p keys
    ~/.cargo/bin/casper-client keygen keys/
fi

# Load public key hex
PUBLIC_KEY_HEX=$(cat "$(dirname "$SECRET_KEY")/public_key_hex")
echo "Using deployer public key: $PUBLIC_KEY_HEX"

# Compile contract
echo "Compiling rwa_risk_registry contract using cargo odra..."
source ~/.cargo/env
cd contracts/rwa_risk_registry
cargo +nightly-2024-09-05 odra build
cd ../..

WASM_PATH="contracts/rwa_risk_registry/wasm/RwaRiskRegistry.wasm"
if [ ! -f "$WASM_PATH" ]; then
    echo "ERROR: Compiled WASM not found at $WASM_PATH"
    exit 1
fi

echo "Deploying $WASM_PATH to Casper Testnet ($NODE_ADDRESS)..."
# Deploy session transaction
TX_JSON=$(~/.cargo/bin/casper-client put-transaction session \
  --wasm-path "$WASM_PATH" \
  --chain-name "$CHAIN_NAME" \
  --gas-price-tolerance 1 \
  --secret-key "$SECRET_KEY" \
  --payment-amount "$PAYMENT_AMOUNT" \
  --standard-payment true \
  --session-arg "odra_cfg_package_hash_key_name:string='rwa_risk_registry'" \
  --session-arg "odra_cfg_allow_key_override:bool='true'" \
  --session-arg "odra_cfg_is_upgradable:bool='false'" \
  --node-address "$NODE_ADDRESS" \
  -vv)

# Extract transaction hash
TX_HASH=$(echo "$TX_JSON" | grep -oE '"transaction_hash": "[a-fA-F0-9]{64}"' | head -n1 | cut -d'"' -f4 || true)
if [ -z "$TX_HASH" ]; then
    # Try alternate grep
    TX_HASH=$(echo "$TX_JSON" | grep -oE '[a-fA-F0-9]{64}' | head -n1 || true)
fi

if [ -z "$TX_HASH" ]; then
    echo "ERROR: Failed to extract transaction hash from deploy response:"
    echo "$TX_JSON"
    exit 1
fi

echo "Deploy submitted successfully!"
echo "Transaction Hash: $TX_HASH"
echo "Explorer Link: https://testnet.cspr.live/deploy/$TX_HASH"

echo "Waiting for transaction to execute (this typically takes 1-2 minutes on Casper Testnet)..."
# We will poll get-transaction until execution status is success
for i in {1..30}; do
    STATUS_JSON=$(~/.cargo/bin/casper-client get-transaction --transaction-hash "$TX_HASH" --node-address "$NODE_ADDRESS" -vv 2>/dev/null || true)
    if echo "$STATUS_JSON" | grep -q '"ExecutionResult"'; then
        if echo "$STATUS_JSON" | grep -q '"Success"'; then
            echo "Transaction executed successfully!"
            break
        else
            echo "Transaction execution failed! Status response:"
            echo "$STATUS_JSON"
            exit 1
        fi
    fi
    sleep 10
done

echo "Querying account named keys to find the contract hash..."
ACCOUNT_JSON=$(~/.cargo/bin/casper-client get-account --account-identifier "$PUBLIC_KEY_HEX" --node-address "$NODE_ADDRESS" -vv || true)

# Grep for rwa_risk_registry key
CONTRACT_HASH=$(echo "$ACCOUNT_JSON" | grep -A 2 -E '"name": "rwa_risk_registry"' | grep -oE '"hash-[a-fA-F0-9]{64}"' | head -n1 | tr -d '"' || true)
if [ -z "$CONTRACT_HASH" ]; then
    # Try alternate search
    CONTRACT_HASH=$(echo "$ACCOUNT_JSON" | grep -oE 'hash-[a-fA-F0-9]{64}' | head -n1 || true)
fi

if [ -z "$CONTRACT_HASH" ]; then
    echo "WARNING: Could not find 'rwa_risk_registry' contract hash in named keys."
    echo "Your account named keys: $ACCOUNT_JSON"
    echo "Please set CASPER_CONTRACT_HASH in agent/.env manually once it executes."
else
    echo "Found contract hash: $CONTRACT_HASH"
    # Update or create agent/.env
    echo "Updating agent/.env..."
    mkdir -p agent
    # Copy from env.example first if not exists
    if [ ! -f agent/.env ]; then
        cp agent/.env.example agent/.env
    fi
    
    # Replace contract hash in agent/.env
    # Handle macOS compatibility for sed
    sed -i.bak -E "s/CASPER_CONTRACT_HASH=.*/CASPER_CONTRACT_HASH=$CONTRACT_HASH/" agent/.env || sed -i "" -E "s/CASPER_CONTRACT_HASH=.*/CASPER_CONTRACT_HASH=$CONTRACT_HASH/" agent/.env
    sed -i.bak -E "s/AGENT_MODE=.*/AGENT_MODE=real/" agent/.env || sed -i "" -E "s/AGENT_MODE=.*/AGENT_MODE=real/" agent/.env
    sed -i.bak -E "s/CASPER_SECRET_KEY_PATH=.*/CASPER_SECRET_KEY_PATH=$(echo "$SECRET_KEY" | sed 's/\//\\\//g')/" agent/.env || sed -i "" -E "s/CASPER_SECRET_KEY_PATH=.*/CASPER_SECRET_KEY_PATH=$(echo "$SECRET_KEY" | sed 's/\//\\\//g')/" agent/.env
    sed -i.bak -E "s/CASPER_PUBLIC_KEY_PATH=.*/CASPER_PUBLIC_KEY_PATH=$(echo "$(dirname "$SECRET_KEY")/public_key.pem" | sed 's/\//\\\//g')/" agent/.env || sed -i "" -E "s/CASPER_PUBLIC_KEY_PATH=.*/CASPER_PUBLIC_KEY_PATH=$(echo "$(dirname "$SECRET_KEY")/public_key.pem" | sed 's/\//\\\//g')/" agent/.env
    sed -i.bak -E "s/CASPER_NODE_ADDRESS=.*/CASPER_NODE_ADDRESS=$(echo "$NODE_ADDRESS" | sed 's/\//\\\//g')/" agent/.env || sed -i "" -E "s/CASPER_NODE_ADDRESS=.*/CASPER_NODE_ADDRESS=$(echo "$NODE_ADDRESS" | sed 's/\//\\\//g')/" agent/.env
    sed -i.bak -E "s/CASPER_DRY_RUN=.*/CASPER_DRY_RUN=false/" agent/.env || sed -i "" -E "s/CASPER_DRY_RUN=.*/CASPER_DRY_RUN=false/" agent/.env
    
    echo "agent/.env successfully updated!"
fi
