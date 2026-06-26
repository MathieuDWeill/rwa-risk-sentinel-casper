from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import hashlib

from .casper_client import CasperPublisher
from .risk_model import fetch_asset_signals, score_signals, now_ms
from .models import AssetSignals

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


@app.post("/uploads/assess")
async def assess_uploaded_document(
    file: UploadFile = File(...),
    should_publish: bool = True,
) -> dict[str, Any]:
    # Ensure uploads directory exists
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    # Save uploaded file locally
    file_path = uploads_dir / file.filename
    content = await file.read()
    with file_path.open("wb") as f:
        f.write(content)

    # Compute sha256 of raw file content
    file_sha256 = hashlib.sha256(content).hexdigest()

    # Parse or generate signals
    is_json = False
    parsed_data = {}
    if file.filename.endswith(".json") or file.content_type == "application/json":
        try:
            parsed_data = json.loads(content.decode("utf-8"))
            is_json = True
        except Exception:
            pass

    if is_json:
        # For JSON, parse fields if present
        asset_id = parsed_data.get("asset_id") or Path(file.filename).stem
        signals = AssetSignals(
            asset_id=asset_id,
            asset_type=parsed_data.get("asset_type", "invoice"),
            payment_delay_days=int(parsed_data.get("payment_delay_days", 0)),
            debtor_credit_score=int(parsed_data.get("debtor_credit_score", 700)),
            macro_volatility_bps=int(parsed_data.get("macro_volatility_bps", 100)),
            collateral_price_change_bps=int(parsed_data.get("collateral_price_change_bps", 0)),
            negative_news_count=int(parsed_data.get("negative_news_count", 0)),
            registry_status=parsed_data.get("registry_status", "active"),
            source_count=int(parsed_data.get("source_count", 3)),
            timestamp_ms=now_ms(),
            raw={"parsed_from_json": True, "original_filename": file.filename}
        )
    else:
        # For TXT/CSV/PDF or unknown, create deterministic synthetic signal profile based on hash
        # and set asset_id from filename stem
        asset_id = Path(file.filename).stem
        seed = int(file_sha256[:8], 16)
        
        signals = AssetSignals(
            asset_id=asset_id,
            asset_type="invoice",
            payment_delay_days=seed % 30,
            debtor_credit_score=500 + (seed % 220),
            macro_volatility_bps=80 + (seed % 400),
            collateral_price_change_bps=-(seed % 900),
            negative_news_count=seed % 5,
            registry_status="active" if (seed % 2 == 0) else "suspended",
            source_count=3 + (seed % 3),
            timestamp_ms=now_ms(),
            raw={"synthetic_from_hash": True, "seed": seed, "original_filename": file.filename}
        )

    # Score signals with file metadata
    report = score_signals(signals, file_sha256=file_sha256, original_filename=file.filename)

    # Save evidence file
    evidence_path = EVIDENCE_DIR / f"{report.asset_id}-{report.timestamp_ms}.json"
    evidence_path.write_text(json.dumps(report.evidence, indent=2), encoding="utf-8")

    # Determine dry_run exactly like /agent/run
    dry_run = True
    env_dry_run = os.getenv("CASPER_DRY_RUN", "true").lower()
    if env_dry_run == "false":
        dry_run = False

    if not should_publish:
        dry_run = True

    # Publish to Casper
    tx = publisher.publish(report, dry_run=dry_run)

    result = {
        "report": report.model_dump(),
        "evidence_path": str(evidence_path),
        "casper": tx,
        # Expose Casper fields at the top-level
        "mode": tx.get("mode"),
        "dry_run": tx.get("dry_run"),
        "submitted": tx.get("submitted"),
        "deploy_hash": tx.get("deploy_hash"),
        "transaction_hash": tx.get("transaction_hash"),
        "explorer_url": tx.get("explorer_url"),
        "contract_hash": tx.get("contract_hash"),
        "package_hash": tx.get("package_hash"),
        # Include file metadata
        "file_sha256": file_sha256,
        "original_filename": file.filename
    }
    RUNS.append(result)
    return result


@app.get("/agent/runs")
def runs() -> dict[str, Any]:
    return {"runs": RUNS[-50:]}


if __name__ == "__main__":
    uvicorn.run("agent.app.main:app", host="0.0.0.0", port=8080, reload=True)
