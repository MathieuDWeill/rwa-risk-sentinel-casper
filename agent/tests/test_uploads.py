import io
import json
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from agent.app.main import app
from agent.app.models import RiskBand
from agent.app.risk_model import score_signals, AssetSignals

client = TestClient(app)


def test_file_hashing():
    # Test that hashing works deterministically
    content = b"rwa-test-content-123"
    expected_hash = hashlib.sha256(content).hexdigest()
    
    # Send request to upload endpoint (mocking dry run so no real Casper Tx is sent)
    response = client.post(
        "/uploads/assess?should_publish=false",
        files={"file": ("test_doc.txt", io.BytesIO(content), "text/plain")}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["file_sha256"] == expected_hash
    assert res_data["original_filename"] == "test_doc.txt"


def test_json_upload_parsing():
    # Construct a valid JSON signal file
    json_signals = {
        "asset_id": "invoice-xyz-999",
        "asset_type": "invoice",
        "payment_delay_days": 15,
        "debtor_credit_score": 620,
        "macro_volatility_bps": 220,
        "collateral_price_change_bps": -450,
        "negative_news_count": 3,
        "registry_status": "active",
        "source_count": 4
    }
    content = json.dumps(json_signals).encode("utf-8")
    
    response = client.post(
        "/uploads/assess?should_publish=false",
        files={"file": ("signals.json", io.BytesIO(content), "application/json")}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    
    # Assert fields are parsed and correct
    report = res_data["report"]
    assert report["asset_id"] == "invoice-xyz-999"
    assert report["score_bps"] > 500  # Penalties applied
    assert report["band"] in [RiskBand.MEDIUM.value, RiskBand.HIGH.value, RiskBand.CRITICAL.value]
    
    # Assert file metadata is present in evidence
    evidence = report["evidence"]
    assert evidence["file_sha256"] == hashlib.sha256(content).hexdigest()
    assert evidence["original_filename"] == "signals.json"
    assert evidence["signals"]["payment_delay_days"] == 15
    assert evidence["signals"]["debtor_credit_score"] == 620


def test_json_upload_missing_fields_defaults():
    # JSON with only asset_id and debtor_credit_score; others should fall back to default values
    json_signals = {
        "asset_id": "invoice-missing-fields",
        "debtor_credit_score": 750
    }
    content = json.dumps(json_signals).encode("utf-8")
    
    response = client.post(
        "/uploads/assess?should_publish=false",
        files={"file": ("partial.json", io.BytesIO(content), "application/json")}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    signals_parsed = res_data["report"]["evidence"]["signals"]
    
    assert signals_parsed["asset_id"] == "invoice-missing-fields"
    assert signals_parsed["debtor_credit_score"] == 750
    # Defaults
    assert signals_parsed["asset_type"] == "invoice"
    assert signals_parsed["payment_delay_days"] == 0
    assert signals_parsed["macro_volatility_bps"] == 100
    assert signals_parsed["registry_status"] == "active"


def test_synthetic_signal_profile_non_json():
    # PDF or other unknown formats should generate deterministic signals from hash
    content = b"pdf-dummy-bytes-102938"
    file_sha256 = hashlib.sha256(content).hexdigest()
    seed = int(file_sha256[:8], 16)
    
    response = client.post(
        "/uploads/assess?should_publish=false",
        files={"file": ("contract.pdf", io.BytesIO(content), "application/pdf")}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    
    # Assert asset_id is stem of filename
    assert res_data["report"]["asset_id"] == "contract"
    
    signals_parsed = res_data["report"]["evidence"]["signals"]
    # Check deterministic formulas
    assert signals_parsed["payment_delay_days"] == seed % 30
    assert signals_parsed["debtor_credit_score"] == 500 + (seed % 220)
    assert signals_parsed["macro_volatility_bps"] == 80 + (seed % 400)
    assert signals_parsed["raw"]["synthetic_from_hash"] is True
