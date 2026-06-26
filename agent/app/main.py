from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .casper_client import CasperPublisher
from .risk_model import fetch_asset_signals, score_signals

load_dotenv()

app = FastAPI(title="RWA Risk Sentinel Agent", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

publisher = CasperPublisher()
EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "evidence"))
EVIDENCE_DIR.mkdir(exist_ok=True)
RUNS: list[dict[str, Any]] = []


class RunRequest(BaseModel):
    asset_id: str = "invoice-2026-001"
    dry_run: bool | None = None
    should_publish: bool | None = None
    force_publish: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rwa-risk-sentinel-agent"}


@app.get("/assets")
def assets() -> dict[str, Any]:
    return {
        "assets": ["invoice-2026-001", "carbon-credit-kenya-042", "real-estate-note-nyc-17"],
        "latest_runs": RUNS[-10:],
    }


@app.get("/assets/{asset_id}/preview")
def preview(asset_id: str) -> dict[str, Any]:
    return score_signals(fetch_asset_signals(asset_id)).model_dump()


@app.post("/agent/run")
def run_agent(req: RunRequest) -> dict[str, Any]:
    signals = fetch_asset_signals(req.asset_id)
    report = score_signals(signals)

    evidence_path = EVIDENCE_DIR / f"{report.asset_id}-{report.timestamp_ms}.json"
    evidence_path.write_text(json.dumps(report.evidence, indent=2), encoding="utf-8")

    # Determine dry_run:
    dry_run = True
    env_dry_run = os.getenv("CASPER_DRY_RUN", "true").lower()
    if env_dry_run == "false":
        dry_run = False
        
    if req.dry_run is not None:
        dry_run = req.dry_run
    elif req.should_publish is not None:
        dry_run = not req.should_publish

    tx = publisher.publish(report, dry_run=dry_run)
    result = {
        "report": report.model_dump(),
        "evidence_path": str(evidence_path),
        "casper": tx,
        # Expose Casper fields at the top-level of the JSON response
        "mode": tx.get("mode"),
        "dry_run": tx.get("dry_run"),
        "submitted": tx.get("submitted"),
        "deploy_hash": tx.get("deploy_hash"),
        "transaction_hash": tx.get("transaction_hash"),
        "explorer_url": tx.get("explorer_url"),
        "contract_hash": tx.get("contract_hash"),
        "package_hash": tx.get("package_hash"),
    }
    RUNS.append(result)
    return result


@app.get("/agent/runs")
def runs() -> dict[str, Any]:
    return {"runs": RUNS[-50:]}


if __name__ == "__main__":
    uvicorn.run("agent.app.main:app", host="0.0.0.0", port=8080, reload=True)
