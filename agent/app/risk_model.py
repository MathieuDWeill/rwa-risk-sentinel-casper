from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .models import AssetSignals, RiskBand, RiskReport

DATA_DIR = Path(__file__).resolve().parents[2] / ".." / "data" / "sample_signals"


def now_ms() -> int:
    return int(time.time() * 1000)


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def fetch_asset_signals(asset_id: str) -> AssetSignals:
    """Fetch asset signals.

    The hackathon demo uses deterministic local data so judges can reproduce it.
    Replace this function with real APIs later: invoice platform, registry, market data,
    weather, shipping, credit bureau, proof provider, etc.
    """
    path = DATA_DIR / f"{asset_id}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["timestamp_ms"] = now_ms()
        return AssetSignals(**data)

    # Fallback signal set with deterministic variation from the asset id.
    seed = int(hashlib.sha256(asset_id.encode()).hexdigest()[:8], 16)
    return AssetSignals(
        asset_id=asset_id,
        payment_delay_days=seed % 18,
        debtor_credit_score=560 + seed % 220,
        macro_volatility_bps=80 + seed % 500,
        collateral_price_change_bps=-(seed % 900),
        negative_news_count=seed % 4,
        registry_status="active",
        source_count=3 + seed % 3,
        timestamp_ms=now_ms(),
        raw={"synthetic_seed": seed},
    )


def risk_band(score_bps: int) -> RiskBand:
    if score_bps >= 8000:
        return RiskBand.CRITICAL
    if score_bps >= 6000:
        return RiskBand.HIGH
    if score_bps >= 3000:
        return RiskBand.MEDIUM
    return RiskBand.LOW


def score_signals(
    signals: AssetSignals,
    file_sha256: str | None = None,
    original_filename: str | None = None,
) -> RiskReport:
    reasons: list[str] = []
    score = 500

    if signals.payment_delay_days > 0:
        added = min(3000, signals.payment_delay_days * 180)
        score += added
        reasons.append(f"Payment delay adds {added} bps risk ({signals.payment_delay_days} days late).")
    else:
        reasons.append("No payment delay detected.")

    credit_penalty = max(0, 720 - signals.debtor_credit_score) * 8
    if credit_penalty:
        score += min(2200, credit_penalty)
        reasons.append(f"Debtor credit score below 720 adds {min(2200, credit_penalty)} bps.")
    else:
        reasons.append("Debtor credit score is healthy.")

    macro_penalty = min(1800, max(0, signals.macro_volatility_bps - 100) * 3)
    score += macro_penalty
    if macro_penalty:
        reasons.append(f"Macro volatility adds {macro_penalty} bps.")

    if signals.collateral_price_change_bps < 0:
        collateral_penalty = min(1800, abs(signals.collateral_price_change_bps) * 2)
        score += collateral_penalty
        reasons.append(f"Collateral drawdown adds {collateral_penalty} bps.")

    news_penalty = min(1200, signals.negative_news_count * 300)
    score += news_penalty
    if news_penalty:
        reasons.append(f"Negative news adds {news_penalty} bps.")

    if signals.registry_status.lower() != "active":
        score += 2500
        reasons.append(f"Registry status is {signals.registry_status}; major risk penalty applied.")

    score_bps = max(0, min(10000, score))
    confidence_bps = max(3500, min(9500, 5200 + signals.source_count * 700))
    band = risk_band(score_bps)

    evidence = {
        "schema": "rwa-risk-sentinel/evidence/v1",
        "signals": signals.model_dump(),
        "model": {
            "name": "deterministic-weighted-risk-v1",
            "score_bps": score_bps,
            "confidence_bps": confidence_bps,
            "band": band.value,
            "reasons": reasons,
        },
    }
    if file_sha256 is not None:
        evidence["file_sha256"] = file_sha256
    if original_filename is not None:
        evidence["original_filename"] = original_filename

    evidence_hash = canonical_hash(evidence)
    summary = f"{band.value} risk for {signals.asset_id}: score {score_bps / 100:.2f}%, confidence {confidence_bps / 100:.2f}%."

    return RiskReport(
        asset_id=signals.asset_id,
        score_bps=score_bps,
        confidence_bps=confidence_bps,
        band=band,
        summary=summary,
        reasons=reasons,
        timestamp_ms=signals.timestamp_ms,
        evidence_hash=evidence_hash,
        evidence=evidence,
        should_publish=True,
    )
