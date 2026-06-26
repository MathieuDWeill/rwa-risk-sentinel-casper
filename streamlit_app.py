import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8080"

st.set_page_config(
    page_title="RWA Intelligence Lab",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --ink: #111318;
  --panel: #181a20;
  --paper: #f4f1e8;
  --line: #111318;
  --red: #ef3838;
  --blue: #173f73;
  --yellow: #f4bd2a;
  --muted: #6c6f78;
  --green: #22c55e;
}

.stApp {
  background: var(--paper);
  color: var(--ink);
}

section[data-testid="stSidebar"] {
  background: #17191f;
  color: #f4f1e8;
  border-right: 4px solid #111318;
}

section[data-testid="stSidebar"] * {
  color: #f4f1e8 !important;
}

section[data-testid="stSidebar"] .hashbox,
section[data-testid="stSidebar"] .hashbox * {
  color: #111318 !important;
  background: #f4f1e8 !important;
}

section[data-testid="stSidebar"] a,
section[data-testid="stSidebar"] a * {
  color: #111318 !important;
}

.block-container {
  padding-top: 2.2rem;
  max-width: 1320px;
}

.lab-hero {
  border: 4px solid var(--line);
  background: #f8f4ea;
  padding: 28px 34px;
  margin-bottom: 20px;
  box-shadow: 10px 10px 0 #111318;
  position: relative;
}

.lab-kicker {
  color: var(--red);
  font-weight: 900;
  letter-spacing: 0.55em;
  font-size: 0.78rem;
  text-transform: uppercase;
}

.lab-title {
  font-size: 3.1rem;
  font-weight: 950;
  line-height: 0.95;
  margin-top: 8px;
  margin-bottom: 12px;
  letter-spacing: -0.04em;
}

.lab-subtitle {
  font-size: 1.05rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.lab-author {
  margin-top: 18px;
  font-size: 0.82rem;
  font-weight: 900;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #111318;
}

.hero-grid {
  position: absolute;
  right: 28px;
  top: 28px;
  display: grid;
  grid-template-columns: 72px 72px 72px;
  grid-template-rows: 58px 58px;
  gap: 8px;
}

.hero-cell {
  border: 4px solid #111318;
  background: #f4f1e8;
}

.hero-cell.red { background: var(--red); }
.hero-cell.blue { background: var(--blue); }
.hero-cell.yellow { background: var(--yellow); }

.metric-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.metric-card {
  background: #17191f;
  color: #f4f1e8;
  border: 3px solid #111318;
  border-top: 6px solid var(--red);
  padding: 18px 20px;
  min-height: 118px;
}

.metric-card.yellow {
  border-top-color: var(--yellow);
}

.metric-card.blue {
  border-top-color: var(--blue);
}

.metric-label {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  font-weight: 900;
  text-transform: uppercase;
  color: #d7d1c5;
}

.metric-value {
  font-size: 1.85rem;
  font-weight: 950;
  margin-top: 10px;
}

.metric-note {
  color: #d7d1c5;
  font-size: 0.88rem;
  margin-top: 4px;
}

.lab-panel {
  border: 3px solid #111318;
  background: #fbf8ef;
  padding: 20px 22px;
  margin-bottom: 18px;
  box-shadow: 6px 6px 0 #111318;
}

.panel-red {
  border-left: 8px solid var(--red);
}

.panel-blue {
  border-left: 8px solid var(--blue);
}

.panel-yellow {
  border-left: 8px solid var(--yellow);
}

.panel-title {
  font-size: 1.35rem;
  font-weight: 950;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  margin-bottom: 10px;
}

.badge {
  display: inline-block;
  border: 2px solid #111318;
  background: #f4f1e8;
  color: #111318;
  padding: 4px 8px;
  font-size: 0.72rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-right: 6px;
}

.badge-red {
  background: var(--red);
  color: white;
}

.badge-green {
  background: var(--green);
  color: white;
}

.badge-yellow {
  background: var(--yellow);
  color: #111318;
}

code {
  font-size: 0.82rem !important;
}

div.stButton > button {
  border: 3px solid #111318;
  border-radius: 0;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  box-shadow: 4px 4px 0 #111318;
}

div.stButton > button[kind="primary"] {
  background: var(--red);
  color: white;
}

div[data-testid="stMetric"] {
  background: #f8f4ea;
  border: 3px solid #111318;
  padding: 12px 14px;
}

.sidebar-logo {
  border: 2px solid #f4f1e8;
  width: 54px;
  height: 54px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 5px;
  margin-bottom: 14px;
}
.sidebar-logo div { border: 1px solid #f4f1e8; }
.sidebar-logo .r { background: var(--red); }
.sidebar-logo .b { background: var(--blue); }
.sidebar-logo .y { background: var(--yellow); }
.sidebar-logo .p { background: var(--paper); }

.sidebar-title {
  font-weight: 950;
  font-size: 1.15rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sidebar-sub {
  color: #cfc8ba !important;
  letter-spacing: 0.22em;
  font-size: 0.78rem;
  text-transform: uppercase;
  margin-bottom: 30px;
}

.sidebar-proof-label {
  color: #cfc8ba !important;
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-top: 12px;
  margin-bottom: 4px;
}

.sidebar-proof-value {
  display: block;
  background: #242730 !important;
  color: #f4f1e8 !important;
  border: 1px solid #3a3d45;
  padding: 8px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.76rem;
  font-weight: 900;
  letter-spacing: 0.02em;
  overflow: hidden;
  white-space: nowrap;
}

.side-link {
  display: block;
  background: #f4f1e8 !important;
  color: #111318 !important;
  border: 2px solid #f4f1e8;
  padding: 10px 12px;
  text-decoration: none !important;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.75rem;
  margin-top: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
<div class="sidebar-logo">
  <div class="p"></div><div class="r"></div>
  <div class="b"></div><div class="y"></div>
</div>
<div class="sidebar-title">RWA INTELLIGENCE LAB</div>
<div class="sidebar-sub">AGENTIC RISK INFRASTRUCTURE</div>
<div class="sidebar-sub">MATHIEU D. WEILL</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### SYSTEM STATUS")
    st.markdown('<span class="badge badge-green">Decision system online</span>', unsafe_allow_html=True)

    st.markdown("### CASPER TESTNET")
    st.markdown(
        '<div class="sidebar-proof-label">CONTRACT</div>'
        '<div class="sidebar-proof-value">725268e3…676609d5</div>'
        '<div class="sidebar-proof-label">LATEST TX</div>'
        '<div class="sidebar-proof-value">7f6848d0…33df7851</div>'
        '<a class="side-link" href="https://testnet.cspr.live/deploy/7f6848d02c5bf1f14618c389c3340efc4026f8328f2b35a875a3eb9f33df7851" target="_blank">Open explorer</a>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="lab-hero">
  <div class="lab-kicker">MODERNIST</div>
  <div class="lab-title">RWA Intelligence Lab</div>
  <div class="lab-subtitle">Survival > Prediction. Evidence before trust.</div>
  <div class="lab-author">Built by Mathieu D. WEILL</div>
  <div class="hero-grid">
    <div class="hero-cell blue"></div>
    <div class="hero-cell"></div>
    <div class="hero-cell red"></div>
    <div class="hero-cell"></div>
    <div class="hero-cell yellow"></div>
    <div class="hero-cell"></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Agent Mode</div>
    <div class="metric-value">On-chain</div>
    <div class="metric-note">Casper Testnet publishing</div>
  </div>
  <div class="metric-card yellow">
    <div class="metric-label">Asset Class</div>
    <div class="metric-value">RWA</div>
    <div class="metric-note">Invoices, carbon, real estate</div>
  </div>
  <div class="metric-card blue">
    <div class="metric-label">Evidence</div>
    <div class="metric-value">Hashed</div>
    <div class="metric-note">AI decision trail</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Casper Proof</div>
    <div class="metric-value">Live</div>
    <div class="metric-note">Transaction-producing component</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="lab-panel panel-blue">
  <div class="panel-title">Teaching companion.</div>
  <strong>Use the app to test an autonomous RWA risk agent on Casper Testnet.</strong>
  <br/>
  The agent observes off-chain signals, scores the asset, hashes the evidence trail, and publishes a verifiable attestation.
</div>
""",
    unsafe_allow_html=True,
)

try:
    assets_resp = requests.get(f"{API_BASE}/assets", timeout=5)
    assets_resp.raise_for_status()
    assets = assets_resp.json().get("assets", [])
except Exception as exc:
    st.error(f"Could not reach FastAPI agent at {API_BASE}: {exc}")
    st.stop()

st.markdown('<div class="lab-panel panel-red"><div class="panel-title">RWA Decision Console</div>', unsafe_allow_html=True)

asset_id = st.selectbox("Asset / Instrument", assets, index=0)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 1. Risk assessment")
    st.markdown(
        '<span class="badge">Universe: Tokenized RWA</span><span class="badge">Model: deterministic-weighted-risk-v1</span>',
        unsafe_allow_html=True,
    )

    if st.button("Preview assessment", use_container_width=True):
        with st.spinner("Evaluating RWA signals..."):
            preview_resp = requests.get(f"{API_BASE}/assets/{asset_id}/preview", timeout=20)
            preview_resp.raise_for_status()
            st.session_state["preview"] = preview_resp.json()

    if "preview" in st.session_state:
        preview = st.session_state["preview"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Risk score", f"{preview['score_bps'] / 100:.2f}%")
        m2.metric("Confidence", f"{preview['confidence_bps'] / 100:.2f}%")
        m3.metric("Risk band", preview["band"])

        if preview["band"] == "HIGH":
            st.markdown('<span class="badge badge-red">High risk</span>', unsafe_allow_html=True)
        elif preview["band"] == "MEDIUM":
            st.markdown('<span class="badge badge-yellow">Medium risk</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-green">Low risk</span>', unsafe_allow_html=True)

        st.markdown("#### Decision factors")
        for reason in preview["reasons"]:
            st.write(f"✓ {reason}")

        st.markdown("#### Evidence hash")
        st.code(preview["evidence_hash"], language="text")

with col2:
    st.markdown("### 2. Casper publication")
    st.markdown(
        '<span class="badge">Network: Casper Testnet</span><span class="badge">Entrypoint: publish_attestation</span>',
        unsafe_allow_html=True,
    )

    if st.button("Run agent + publish on Casper Testnet", type="primary", use_container_width=True):
        with st.spinner("Submitting attestation to Casper Testnet..."):
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
            st.markdown('<span class="badge badge-green">Real Casper transaction submitted</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-red">Not a real Testnet submission</span>', unsafe_allow_html=True)
            st.json(casper)

        m1, m2, m3 = st.columns(3)
        m1.metric("Mode", casper.get("mode"))
        m2.metric("Submitted", str(casper.get("submitted")))
        m3.metric("Dry run", str(casper.get("dry_run")))

        st.markdown("#### Transaction hash")
        st.code(casper.get("transaction_hash") or casper.get("deploy_hash"), language="text")

        st.markdown("#### Contract hash")
        st.code(casper.get("contract_hash"), language="text")

        explorer_url = casper.get("explorer_url")
        if explorer_url:
            st.link_button("Open Casper Testnet Explorer", explorer_url, use_container_width=True)

        st.markdown("#### Evidence hash")
        st.code(result["report"]["evidence_hash"], language="text")

        with st.expander("Full agent response"):
            st.json(result)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
<div class="lab-panel panel-yellow">
  <div class="panel-title">Agent Loop</div>
  <span class="badge">Observe</span>
  <span class="badge">Evaluate</span>
  <span class="badge">Hash Evidence</span>
  <span class="badge">Decide</span>
  <span class="badge">Publish</span>
  <span class="badge">Verify</span>
  <br/><br/>
  <strong>Not just AI opinions — verifiable Casper attestations.</strong>
</div>
""",
    unsafe_allow_html=True,
)
