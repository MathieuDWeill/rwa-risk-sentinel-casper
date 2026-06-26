#!/usr/bin/env bash
set -euo pipefail

echo "Loading environment variables from agent/.env..."
if [ -f agent/.env ]; then
    export $(grep -v '^#' agent/.env | xargs)
else
    echo "ERROR: agent/.env file not found. Run deploy script or copy agent/.env.example first."
    exit 1
fi

echo "Verifying environment variables..."
REQUIRED_VARS=(
    "CASPER_NODE_ADDRESS"
    "CASPER_CHAIN_NAME"
    "CASPER_SECRET_KEY_PATH"
    "CASPER_CONTRACT_HASH"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: Required environment variable $var is empty or not set."
        exit 1
    fi
done

echo "Running agent risk Sentinel analysis for verification..."
RESPONSE_JSON=$(curl -s -X POST http://127.0.0.1:8080/agent/run \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"invoice-2026-001"}')

echo "Response received:"
if command -v python3 &>/dev/null; then
    echo "$RESPONSE_JSON" | python3 -m json.tool || echo "$RESPONSE_JSON"
else
    echo "$RESPONSE_JSON"
fi

if command -v python3 &>/dev/null; then
    MODE=$(echo "$RESPONSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('casper', {}).get('mode', ''))" || true)
    DRY_RUN=$(echo "$RESPONSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('casper', {}).get('dry_run', ''))" || true)
    SUBMITTED=$(echo "$RESPONSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('casper', {}).get('submitted', ''))" || true)
    DEPLOY_HASH=$(echo "$RESPONSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('casper', {}).get('deploy_hash', ''))" || true)
    EXPLORER_URL=$(echo "$RESPONSE_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('casper', {}).get('explorer_url', ''))" || true)
else
    # Simple grep fallbacks if python3 is not available (though it is)
    MODE=$(echo "$RESPONSE_JSON" | grep -oE '"mode": "[^"]+"' | head -n1 | cut -d'"' -f4 || true)
    DRY_RUN=$(echo "$RESPONSE_JSON" | grep -oE '"dry_run": (true|false)' | head -n1 | cut -d' ' -f2 || true)
    SUBMITTED=$(echo "$RESPONSE_JSON" | grep -oE '"submitted": (true|false)' | head -n1 | cut -d' ' -f2 || true)
    DEPLOY_HASH=$(echo "$RESPONSE_JSON" | grep -oE '"deploy_hash": "[^"]+"' | head -n1 | cut -d'"' -f4 || true)
    EXPLORER_URL=$(echo "$RESPONSE_JSON" | grep -oE '"explorer_url": "[^"]+"' | head -n1 | cut -d'"' -f4 || true)
fi

# Validations
if [ "$MODE" = "mock" ] || [ "$MODE" = "mock-dry-run" ]; then
    echo "ERROR: Publisher is still running in 'mock' mode (mode: $MODE)!"
    exit 1
fi

if [ "$DRY_RUN" = "True" ] || [ "$DRY_RUN" = "true" ]; then
    echo "ERROR: Execution was a dry_run!"
    exit 1
fi

if [ "$SUBMITTED" != "True" ] && [ "$SUBMITTED" != "true" ]; then
    echo "ERROR: Submitted flag is not true!"
    exit 1
fi

if [ -z "$DEPLOY_HASH" ] || [ "$DEPLOY_HASH" = "null" ]; then
    echo "ERROR: Deploy hash is empty!"
    exit 1
fi

echo "SUCCESS: Real Casper Testnet transaction verified!"
echo "Deploy Hash: $DEPLOY_HASH"
echo "Explorer URL: $EXPLORER_URL"
