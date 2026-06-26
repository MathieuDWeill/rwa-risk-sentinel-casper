# Demo script

## 0:00 — Problem

Tokenized real-world assets depend on off-chain facts: payment delays, credit deterioration, registry changes, weather, market movement. DeFi protocols need those signals on-chain, but raw off-chain data is not verifiable or easy to automate.

## 0:25 — Solution

RWA Risk Sentinel is an autonomous agent that monitors those signals, computes an explainable risk score, creates an evidence hash, and publishes a compact attestation to Casper.

## 0:50 — Live demo

Run:

```bash
python -m agent.app.main
python scripts/run_demo_cycle.py --asset invoice-2026-001 --count 1
```

Show:

- score;
- reasons;
- evidence hash;
- Casper deploy hash;
- dashboard.

## 1:50 — Why it matters

Any RWA lending, insurance, or collateral protocol can consume the latest score. The agent can evolve into an x402-paid API and MCP tool for machine-to-machine commerce.

## 2:30 — Closing

This is a practical Casper-native building block for the agent economy: autonomous, auditable, and useful for DeFi/RWA.
