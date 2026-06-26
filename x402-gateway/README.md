# x402 Gateway Scaffold

Final-round monetization idea: risk reports become paid machine-to-machine APIs.

Flow:

1. External agent requests `/paid/risk-report/:asset_id`.
2. Gateway requires x402-style payment proof.
3. After payment, gateway calls the Sentinel agent.
4. The report response includes the evidence hash and latest Casper attestation.

This is intentionally a scaffold for the qualification round. Do not block the core Testnet demo on this.
