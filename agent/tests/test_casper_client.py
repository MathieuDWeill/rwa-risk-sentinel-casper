import os
import pytest
from agent.app.models import RiskBand, RiskReport
from agent.app.casper_client import RealCasperPublisher, MockCasperPublisher

def test_mock_publisher_returns_mock_fields():
    report = RiskReport(
        asset_id="test-asset",
        score_bps=1200,
        confidence_bps=9500,
        band=RiskBand.LOW,
        summary="Low risk",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:123",
        evidence={},
        should_publish=True
    )
    publisher = MockCasperPublisher()
    res = publisher.publish(report, dry_run=True)
    assert res["mode"] == "mock"
    assert res["dry_run"] is True
    assert res["submitted"] is False
    assert len(res["deploy_hash"]) == 64
    assert "transaction_hash" in res
    assert "explorer_url" in res
    assert "contract_hash" in res
    assert "package_hash" in res

def test_real_publisher_dry_run_marked():
    report = RiskReport(
        asset_id="test-asset2",
        score_bps=1500,
        confidence_bps=9000,
        band=RiskBand.LOW,
        summary="Low risk2",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:456",
        evidence={},
        should_publish=True
    )
    publisher = RealCasperPublisher(
        node_address="https://node.testnet.casper.network/rpc",
        chain_name="casper-test",
        contract_hash="hash-123",
        secret_key_path="keys/secret_key.pem",
        public_key_path="keys/public_key.pem"
    )
    res = publisher.publish(report, dry_run=True)
    assert res["mode"] == "real-dry-run"
    assert res["dry_run"] is True
    assert res["submitted"] is False
    assert "testnet.cspr.live" in res["explorer_url"]

def test_real_publisher_non_dry_run_fails_without_funded_keys():
    report = RiskReport(
        asset_id="test-asset3",
        score_bps=1500,
        confidence_bps=9000,
        band=RiskBand.LOW,
        summary="Low risk3",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:456",
        evidence={},
        should_publish=True
    )
    publisher = RealCasperPublisher(
        node_address="https://node.testnet.casper.network/rpc",
        chain_name="casper-test",
        contract_hash="hash-123",
        secret_key_path="nonexistent_key.pem",
        public_key_path="nonexistent_public.pem"
    )
    # Real mode must NOT silently mock when dry_run=False. It must run the CLI and fail when key doesn't exist.
    with pytest.raises(Exception):
        publisher.publish(report, dry_run=False)

def test_mock_publisher_never_claims_testnet():
    report = RiskReport(
        asset_id="test-asset-mock-only",
        score_bps=1200,
        confidence_bps=9500,
        band=RiskBand.LOW,
        summary="Low risk",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:123",
        evidence={},
        should_publish=True
    )
    publisher = MockCasperPublisher()
    res = publisher.publish(report, dry_run=False)
    # Even if dry_run=False is requested, MockCasperPublisher must never return mode "testnet"
    assert res["mode"] == "mock"
    assert res["submitted"] is True
    assert res["dry_run"] is False

def test_real_publisher_validates_required_params():
    report = RiskReport(
        asset_id="test-asset-real-invalid",
        score_bps=1200,
        confidence_bps=9500,
        band=RiskBand.LOW,
        summary="Low risk",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:123",
        evidence={},
        should_publish=True
    )
    # Real publisher with empty inputs
    publisher = RealCasperPublisher(
        node_address="",
        chain_name="casper-test",
        contract_hash="",
        secret_key_path="",
        public_key_path=""
    )
    # Calling in dry-run is fine (returns mock-like)
    res_dry = publisher.publish(report, dry_run=True)
    assert res_dry["mode"] == "real-dry-run"
    
    # Non-dry-run must raise ValueError rather than returning fake hashes
    with pytest.raises(ValueError) as excinfo:
        publisher.publish(report, dry_run=False)
    assert "Missing required Casper environment variables" in str(excinfo.value)

def test_casper_publisher_fallback_and_selection(monkeypatch):
    report = RiskReport(
        asset_id="test-asset-select",
        score_bps=1200,
        confidence_bps=9500,
        band=RiskBand.LOW,
        summary="Low risk",
        reasons=[],
        timestamp_ms=1715678900000,
        evidence_hash="sha256:123",
        evidence={},
        should_publish=True
    )
    
    # 1. Clean environment: should fall back to mock
    monkeypatch.delenv("CASPER_NODE_ADDRESS", raising=False)
    monkeypatch.delenv("CASPER_SECRET_KEY_PATH", raising=False)
    monkeypatch.delenv("CASPER_PUBLIC_KEY_PATH", raising=False)
    monkeypatch.delenv("CASPER_CONTRACT_HASH", raising=False)
    
    from agent.app.casper_client import CasperPublisher
    pub = CasperPublisher()
    res = pub.publish(report, dry_run=False)
    assert res["mode"] == "mock"
    
    # 2. Configured environment: calling with dry_run=False should use RealCasperPublisher
    monkeypatch.setenv("CASPER_NODE_ADDRESS", "https://node.testnet.casper.network/rpc")
    monkeypatch.setenv("CASPER_SECRET_KEY_PATH", "nonexistent_key.pem")
    monkeypatch.setenv("CASPER_PUBLIC_KEY_PATH", "nonexistent_public.pem")
    monkeypatch.setenv("CASPER_CONTRACT_HASH", "hash-123")
    
    pub_configured = CasperPublisher()
    # It must fail because files do not exist (raising FileNotFoundError) and NOT silently use mock
    with pytest.raises(FileNotFoundError):
        pub_configured.publish(report, dry_run=False)

