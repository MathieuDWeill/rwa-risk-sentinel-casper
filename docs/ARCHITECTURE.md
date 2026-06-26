# Architecture

## Components

- **Risk Agent:** FastAPI service with an autonomous run endpoint and deterministic demo data source.
- **Risk Engine:** Weighted scoring model that produces score, confidence, reasons, and a canonical evidence hash.
- **Evidence Store:** Local JSON evidence files for demo; production can use IPFS, Arweave, S3, or a verifiable data provider.
- **Casper Contract:** Stores latest attestation per asset and simple publisher reputation.
- **Dashboard:** Judge-friendly UI that explains the agent loop and shows the latest risk preview.
- **MCP Server:** Final-round extension for LLM/agent tooling.
- **x402 Gateway:** Final-round extension for paid agent-to-agent risk APIs.

## On-chain data minimization

The contract stores only:

- asset id;
- risk score in basis points;
- confidence in basis points;
- evidence hash;
- short summary;
- timestamp;
- publisher address.

This avoids writing bulky or private RWA data on-chain while preserving auditability.
