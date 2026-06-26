from __future__ import annotations

import os
import time
import hashlib
import subprocess
import json
from dataclasses import dataclass
from typing import Any, Protocol

from .models import RiskReport


class Publisher(Protocol):
    def publish(self, report: RiskReport, dry_run: bool = True) -> dict[str, Any]: ...


@dataclass
class MockCasperPublisher:
    """Local publisher that behaves like a Casper submitter for demos/tests."""

    def publish(self, report: RiskReport, dry_run: bool = True) -> dict[str, Any]:
        deploy_hash = hashlib.sha256(
            f"{report.asset_id}:{report.evidence_hash}:{time.time_ns()}".encode()
        ).hexdigest()
        return {
            "mode": "mock",
            "dry_run": dry_run,
            "submitted": not dry_run,
            "deploy_hash": deploy_hash,
            "transaction_hash": deploy_hash,
            "explorer_url": "https://testnet.cspr.live",
            "explorer_hint": "Replace with Casper Testnet deploy URL after real integration.",
            "contract_hash": "mock-contract-hash",
            "package_hash": "mock-contract-hash",
            "entry_point": "publish_attestation",
            "args": {
                "asset_id": report.asset_id,
                "score_bps": report.score_bps,
                "confidence_bps": report.confidence_bps,
                "evidence_hash": report.evidence_hash,
                "summary": report.summary,
                "timestamp_ms": report.timestamp_ms,
            },
        }


@dataclass
class RealCasperPublisher:
    node_address: str
    chain_name: str
    contract_hash: str
    secret_key_path: str
    public_key_path: str
    entry_point: str = "publish_attestation"

    def publish(self, report: RiskReport, dry_run: bool = True) -> dict[str, Any]:
        """Publish to Casper Testnet.

        The call must invoke the deployed contract's `publish_attestation` entrypoint.
        """
        if dry_run:
            return MockCasperPublisher().publish(report, dry_run=True) | {
                "mode": "real-dry-run",
                "explorer_url": "https://testnet.cspr.live"
            }

        # Validate paths and contract hash for real publishing
        if not self.secret_key_path or not self.public_key_path or not self.contract_hash:
            raise ValueError(
                "Missing required Casper environment variables: "
                "CASPER_SECRET_KEY_PATH, CASPER_PUBLIC_KEY_PATH, and CASPER_CONTRACT_HASH must be configured for real publishing."
            )

        if not os.path.exists(self.secret_key_path):
            raise FileNotFoundError(f"Casper secret key not found at: {self.secret_key_path}")

        if not os.path.exists(self.public_key_path):
            raise FileNotFoundError(f"Casper public key not found at: {self.public_key_path}")

        # Verify contract hash starts with 'hash-'
        contract_hash_arg = self.contract_hash
        if not contract_hash_arg.startswith("hash-") and not contract_hash_arg.startswith("entity-contract-"):
            contract_hash_arg = f"hash-{contract_hash_arg}"

        # Resolve casper-client path
        casper_client_path = "casper-client"
        cargo_bin_client = os.path.expanduser("~/.cargo/bin/casper-client")
        if os.path.exists(cargo_bin_client):
            casper_client_path = cargo_bin_client

        # Clean string parameters to remove any single quotes
        clean_asset_id = report.asset_id.replace("'", "")
        clean_summary = report.summary.replace("'", "")
        clean_evidence_hash = report.evidence_hash.replace("'", "")

        cmd = [
            casper_client_path,
            "put-transaction",
            "invocable-entity",
            "--node-address", self.node_address,
            "--chain-name", self.chain_name,
            "--secret-key", self.secret_key_path,
            "--contract-hash", contract_hash_arg,
            "--session-entry-point", self.entry_point,
            "--payment-amount", "5000000000",  # 5 CSPR gas fee
            "--standard-payment", "true",
            "--gas-price-tolerance", "1",
            "--session-arg", f"asset_id:string='{clean_asset_id}'",
            "--session-arg", f"score_bps:u32='{report.score_bps}'",
            "--session-arg", f"confidence_bps:u32='{report.confidence_bps}'",
            "--session-arg", f"evidence_hash:string='{clean_evidence_hash}'",
            "--session-arg", f"summary:string='{clean_summary}'",
            "--session-arg", f"timestamp_ms:u64='{report.timestamp_ms}'"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            tx_hash = None
            try:
                out_data = json.loads(result.stdout)
                raw_hash = out_data.get("transaction_hash") or out_data.get("result", {}).get("transaction_hash")
                if isinstance(raw_hash, dict):
                    tx_hash = raw_hash.get("Version1") or list(raw_hash.values())[0]
                else:
                    tx_hash = raw_hash
            except json.JSONDecodeError:
                for line in result.stdout.splitlines():
                    if "transaction_hash" in line or "deploy_hash" in line:
                        parts = line.replace('"', '').replace("'", "").split(":")
                        if len(parts) > 1:
                            tx_hash = parts[-1].strip()
                            break

            if not tx_hash:
                for word in result.stdout.split():
                    if len(word) == 64 and all(c in "0123456789abcdefABCDEF" for c in word):
                        tx_hash = word
                        break

            if not tx_hash:
                tx_hash = "unknown_transaction_hash"

            return {
                "mode": "testnet",
                "dry_run": False,
                "submitted": True,
                "deploy_hash": tx_hash,
                "transaction_hash": tx_hash,
                "explorer_url": f"https://testnet.cspr.live/deploy/{tx_hash}",
                "explorer_hint": f"https://testnet.cspr.live/deploy/{tx_hash}",
                "contract_hash": self.contract_hash,
                "package_hash": self.contract_hash,
                "entry_point": self.entry_point,
                "args": {
                    "asset_id": report.asset_id,
                    "score_bps": report.score_bps,
                    "confidence_bps": report.confidence_bps,
                    "evidence_hash": report.evidence_hash,
                    "summary": report.summary,
                    "timestamp_ms": report.timestamp_ms,
                },
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"casper-client execution failed with exit code {e.returncode}.\n"
                f"Stdout: {e.stdout}\n"
                f"Stderr: {e.stderr}"
            ) from e


class CasperPublisher:
    def __init__(self) -> None:
        pass

    def publish(self, report: RiskReport, dry_run: bool = True) -> dict[str, Any]:
        env_dry_run = os.getenv("CASPER_DRY_RUN", "true").lower()
        mode = os.getenv("AGENT_MODE", "mock").lower()

        has_env_vars = all([
            os.getenv("CASPER_NODE_ADDRESS"),
            os.getenv("CASPER_SECRET_KEY_PATH"),
            os.getenv("CASPER_PUBLIC_KEY_PATH"),
            os.getenv("CASPER_CONTRACT_HASH")
        ])

        if (mode in ("real", "testnet") or env_dry_run == "false" or not dry_run) and has_env_vars:
            impl = RealCasperPublisher(
                node_address=os.getenv("CASPER_NODE_ADDRESS", ""),
                chain_name=os.getenv("CASPER_CHAIN_NAME", "casper-test"),
                contract_hash=os.getenv("CASPER_CONTRACT_HASH", ""),
                secret_key_path=os.getenv("CASPER_SECRET_KEY_PATH", ""),
                public_key_path=os.getenv("CASPER_PUBLIC_KEY_PATH", ""),
                entry_point=os.getenv("CASPER_ENTRY_POINT", "publish_attestation"),
            )
            return impl.publish(report, dry_run=dry_run)

        return MockCasperPublisher().publish(report, dry_run=dry_run)
