from agent.app.models import AssetSignals, RiskBand
from agent.app.risk_model import canonical_hash, score_signals


def test_hash_is_canonical():
    assert canonical_hash({"b": 2, "a": 1}) == canonical_hash({"a": 1, "b": 2})


def test_low_risk_asset_scores_low():
    report = score_signals(AssetSignals(asset_id="safe", timestamp_ms=1, debtor_credit_score=780))
    assert report.score_bps < 3000
    assert report.band == RiskBand.LOW
    assert report.evidence_hash.startswith("sha256:")


def test_bad_registry_status_increases_risk():
    report = score_signals(
        AssetSignals(
            asset_id="bad",
            timestamp_ms=1,
            payment_delay_days=20,
            debtor_credit_score=540,
            macro_volatility_bps=700,
            collateral_price_change_bps=-800,
            negative_news_count=4,
            registry_status="suspended",
        )
    )
    assert report.score_bps >= 8000
    assert report.band == RiskBand.CRITICAL
