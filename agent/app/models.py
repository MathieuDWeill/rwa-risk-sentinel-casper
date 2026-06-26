from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssetSignals(BaseModel):
    asset_id: str
    asset_type: str = "invoice"
    payment_delay_days: int = 0
    debtor_credit_score: int = 700
    macro_volatility_bps: int = 100
    collateral_price_change_bps: int = 0
    negative_news_count: int = 0
    registry_status: str = "active"
    source_count: int = 3
    timestamp_ms: int
    raw: dict[str, Any] = Field(default_factory=dict)


class RiskReport(BaseModel):
    asset_id: str
    score_bps: int
    confidence_bps: int
    band: RiskBand
    summary: str
    reasons: list[str]
    timestamp_ms: int
    evidence_hash: str
    evidence: dict[str, Any]
    should_publish: bool = True
