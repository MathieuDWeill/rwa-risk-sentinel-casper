# Codex finalization prompt

You are finalizing this repo for the Casper Agentic Buildathon 2026 qualification round. Do not rewrite the product concept. Make the prototype transaction-producing on Casper Testnet.

Priority order:

1. Inspect `contracts/rwa_risk_registry` and make it compile with a current Odra/Casper toolchain.
2. Implement `scripts/deploy_contract_placeholder.sh` as a real deploy script.
3. Implement `agent/app/casper_client.py::RealCasperPublisher.publish()` with the chosen SDK/CLI.
4. Preserve the API response shape used by the frontend and `scripts/run_demo_cycle.py`.
5. Add a `docs/TESTNET_TRANSACTIONS.md` file with real deploy hashes and explorer links.
6. Run tests and add one integration smoke test if possible.
7. Keep the README simple and demo-focused.

Definition of done:

- Contract deployed to Casper Testnet.
- Running `AGENT_MODE=real python scripts/run_demo_cycle.py --asset invoice-2026-001 --count 3 --real` produces real deploy hashes.
- Demo video can show at least one transaction in the Casper Testnet explorer.
