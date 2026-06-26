import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8080"

st.set_page_config(
    page_title="RWA Risk Sentinel",
    page_icon="🛰️",
    layout="wide",
)

st.title("🛰️ RWA Risk Sentinel")
st.subheader("Verifiable AI risk attestations for tokenized real-world assets on Casper")

st.markdown(
    """
RWA Risk Sentinel is an autonomous AI agent that evaluates off-chain RWA signals,
generates an evidence hash, and publishes a verifiable attestation to Casper Testnet.
"""
)

with st.sidebar:
    st.header("Casper Testnet Proof")
    st.caption("Contract hash")
    st.code(
        "hash-725268e37535a1bca175840693f9b59ea7dd2accbcbd104577145f82576609d5",
        language="text",
    )
    st.link_button(
        "Latest attestation on Casper Testnet",
        "https://testnet.cspr.live/deploy/7f6848d02c5bf1f14618c389c3340efc4026f8328f2b35a875a3eb9f33df7851",
        use_container_width=True,
    )

try:
    assets_resp = requests.get(f"{API_BASE}/assets", timeout=5)
    assets_resp.raise_for_status()
    assets = assets_resp.json().get("assets", [])
except Exception as exc:
    st.error(f"Could not reach FastAPI agent at {API_BASE}: {exc}")
    st.stop()

asset_id = st.selectbox("Choose an RWA asset", assets, index=0)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 1. Preview risk assessment")

    if st.button("Preview assessment", use_container_width=True):
        with st.spinner("Evaluating RWA signals..."):
            preview_resp = requests.get(
                f"{API_BASE}/assets/{asset_id}/preview",
                timeout=20,
            )
            preview_resp.raise_for_status()
            st.session_state["preview"] = preview_resp.json()

    if "preview" in st.session_state:
        preview = st.session_state["preview"]
        st.metric("Risk score", f"{preview['score_bps'] / 100:.2f}%")
        st.metric("Confidence", f"{preview['confidence_bps'] / 100:.2f}%")
        if preview["band"] == "HIGH":
            st.error(f"Risk band: {preview['band']}")
        elif preview["band"] == "MEDIUM":
            st.warning(f"Risk band: {preview['band']}")
        else:
            st.success(f"Risk band: {preview['band']}")

        st.markdown("#### Reasons")
        for reason in preview["reasons"]:
            st.write(f"- {reason}")

        st.markdown("#### Evidence hash")
        st.code(preview["evidence_hash"], language="text")

with col2:
    st.markdown("### 2. Publish Casper attestation")

    if st.button(
        "Run agent + publish on Casper Testnet",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Running agent and submitting Casper Testnet transaction..."):
            run_resp = requests.post(
                f"{API_BASE}/agent/run",
                json={"asset_id": asset_id},
                timeout=180,
            )
            if run_resp.status_code >= 400:
                st.error(run_resp.text)
                st.stop()
            st.session_state["result"] = run_resp.json()

    if "result" in st.session_state:
        result = st.session_state["result"]
        casper = result.get("casper", {})

        real_success = (
            casper.get("mode") == "testnet"
            and casper.get("dry_run") is False
            and casper.get("submitted") is True
        )

        if real_success:
            st.success("Real Casper Testnet transaction submitted")
        else:
            st.error("Not a real Testnet submission")
            st.json(casper)

        st.metric("Mode", casper.get("mode"))
        st.metric("Submitted", str(casper.get("submitted")))
        st.metric("Dry run", str(casper.get("dry_run")))

        st.markdown("#### Transaction hash")
        st.code(casper.get("transaction_hash") or casper.get("deploy_hash"), language="text")

        st.markdown("#### Contract hash")
        st.code(casper.get("contract_hash"), language="text")

        explorer_url = casper.get("explorer_url")
        if explorer_url:
            st.link_button("Open Casper Testnet Explorer", explorer_url, use_container_width=True)

        st.markdown("#### Evidence hash")
        st.code(result["report"]["evidence_hash"], language="text")

        with st.expander("Full JSON response"):
            st.json(result)

st.markdown("---")
st.markdown(
    """
### Agent loop

`Observe RWA signals → Evaluate risk → Hash evidence → Decide → Publish → Verify`

This demo shows an AI agent producing a machine-readable RWA risk attestation and anchoring it on Casper Testnet.
"""
)
