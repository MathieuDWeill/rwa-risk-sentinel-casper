"use client";

import { useState, useEffect } from "react";

interface RiskReport {
  asset_id: string;
  score_bps: number;
  confidence_bps: number;
  band: string;
  summary: string;
  reasons: string[];
  timestamp_ms: number;
  evidence_hash: string;
  evidence: any;
  should_publish: boolean;
}

interface RunResult {
  report: RiskReport;
  evidence_path: string;
  casper: {
    mode: string;
    dry_run: boolean;
    submitted: boolean;
    deploy_hash: string;
    explorer_hint: string;
    entry_point: string;
    args: any;
  };
}

export default function Home() {
  const [assets, setAssets] = useState<string[]>(["invoice-2026-001", "carbon-credit-kenya-042", "real-estate-note-nyc-17"]);
  const [selectedAsset, setSelectedAsset] = useState<string>("invoice-2026-001");
  const [preview, setPreview] = useState<RiskReport | null>(null);
  const [runs, setRuns] = useState<RunResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [mode, setMode] = useState<"mock" | "real">("mock");
  const [backendUrl, setBackendUrl] = useState<string>("http://localhost:8080");

  // Fetch initial data
  useEffect(() => {
    fetchData();
  }, [backendUrl]);

  const fetchData = async () => {
    try {
      // Fetch assets list and history
      const res = await fetch(`${backendUrl}/assets`);
      if (res.ok) {
        const data = await res.json();
        if (data.assets) setAssets(data.assets);
      }
      
      // Fetch history
      const runsRes = await fetch(`${backendUrl}/agent/runs`);
      if (runsRes.ok) {
        const runsData = await runsRes.json();
        if (runsData.runs) setRuns(runsData.runs.slice().reverse());
      }

      // Fetch active preview for selected asset
      fetchPreview(selectedAsset);
    } catch (err) {
      console.error("Error connecting to agent backend:", err);
    }
  };

  const fetchPreview = async (assetId: string) => {
    try {
      const res = await fetch(`${backendUrl}/assets/${assetId}/preview`);
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
      }
    } catch (err) {
      console.error("Error fetching preview:", err);
    }
  };

  const handleAssetChange = (assetId: string) => {
    setSelectedAsset(assetId);
    fetchPreview(assetId);
  };

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_id: selectedAsset,
          dry_run: mode === "mock",
          force_publish: true
        })
      });
      if (res.ok) {
        const data: RunResult = await res.json();
        // Add to runs list
        setRuns(prev => [data, ...prev]);
        // Update preview
        setPreview(data.report);
      } else {
        alert("Execution failed. Check backend console.");
      }
    } catch (err) {
      console.error("Error running agent:", err);
      alert("Could not reach the agent backend. Ensure it is running on port 8080.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Casper Agentic Buildathon 2026</p>
        <h1>RWA Risk Sentinel</h1>
        <p className="lead">
          An autonomous risk oracle that monitors off-chain asset signals, packages explainable risk evidence,
          and publishes cryptographic proof to Casper Testnet.
        </p>
        <div className="cta" style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            Select Asset: 
            <select 
              value={selectedAsset} 
              onChange={(e) => handleAssetChange(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: 'white',
                padding: '4px 8px',
                marginLeft: '8px',
                cursor: 'pointer'
              }}
            >
              {assets.map(a => <option key={a} value={a} style={{ background: '#0b0f1a' }}>{a}</option>)}
            </select>
          </div>
          <div>
            Mode:
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as "mock" | "real")}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: 'white',
                padding: '4px 8px',
                marginLeft: '8px',
                cursor: 'pointer'
              }}
            >
              <option value="mock" style={{ background: '#0b0f1a' }}>Mock (Dry Run)</option>
              <option value="real" style={{ background: '#0b0f1a' }}>Casper Testnet (Real Tx)</option>
            </select>
          </div>
          <button
            onClick={runAnalysis}
            disabled={loading}
            style={{
              background: loading ? '#475569' : '#2563eb',
              border: 'none',
              borderRadius: '999px',
              color: 'white',
              padding: '10px 20px',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 12px rgba(37,99,235,0.3)',
              transition: 'all 0.2s',
            }}
          >
            {loading ? "Analyzing..." : "Run Risk Analysis 🚀"}
          </button>
        </div>
      </section>

      <section className="grid">
        <div className="card big">
          <h2>Latest risk preview</h2>
          {preview ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="score">{(preview.score_bps / 100).toFixed(2)}%</div>
                <div style={{
                  padding: '6px 12px',
                  borderRadius: '12px',
                  fontWeight: 'bold',
                  background: preview.band === "LOW" ? 'rgba(34,197,94,0.2)' : 
                              preview.band === "MEDIUM" ? 'rgba(234,179,8,0.2)' : 
                              preview.band === "HIGH" ? 'rgba(249,115,22,0.2)' : 'rgba(239,68,68,0.2)',
                  color: preview.band === "LOW" ? '#86efac' : 
                         preview.band === "MEDIUM" ? '#fef08a' : 
                         preview.band === "HIGH" ? '#fed7aa' : '#fecaca',
                  border: '1px solid currentColor'
                }}>
                  {preview.band} RISK
                </div>
              </div>
              <p className="band">Confidence {(preview.confidence_bps / 100).toFixed(2)}%</p>
              <p style={{ fontSize: '18px', color: '#e2e8f0' }}>{preview.summary}</p>
              
              <div style={{ marginTop: '20px' }}>
                <strong>Evidence Package:</strong>
                <code className="hash" style={{ fontSize: '12px', marginTop: '6px' }}>{preview.evidence_hash}</code>
              </div>

              {preview.reasons && preview.reasons.length > 0 && (
                <div style={{ marginTop: '20px' }}>
                  <strong>Risk Assessment Breakdown:</strong>
                  <ul style={{ paddingLeft: '20px', marginTop: '8px' }}>
                    {preview.reasons.map((reason, idx) => (
                      <li key={idx} style={{ color: '#94a3b8', fontSize: '14px' }}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p>Start the agent API on port 8080 to load data.</p>
          )}
        </div>

        <div className="card">
          <h2>Agent Execution Loop</h2>
          <ol style={{ paddingLeft: '20px', margin: '0', fontSize: '15px', lineHeight: '1.8' }}>
            <li>Observe off-chain signals (delay, score, news)</li>
            <li>Evaluate risk & explain findings</li>
            <li>Generate cryptographic evidence hash</li>
            <li>Submit on-chain proof to Casper Network</li>
          </ol>
        </div>

        {runs.length > 0 && (
          <div className="card wide" style={{ marginTop: '18px' }}>
            <h2>On-Chain Execution History</h2>
            <div style={{ overflowX: 'auto', marginTop: '12px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
                    <th style={{ textAlign: 'left', padding: '12px' }}>Asset ID</th>
                    <th style={{ textAlign: 'left', padding: '12px' }}>Score</th>
                    <th style={{ textAlign: 'left', padding: '12px' }}>Band</th>
                    <th style={{ textAlign: 'left', padding: '12px' }}>Casper Deploy Hash</th>
                    <th style={{ textAlign: 'left', padding: '12px' }}>Tx Mode</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#e2e8f0' }}>
                      <td style={{ padding: '12px', fontWeight: 'bold' }}>{run.report.asset_id}</td>
                      <td style={{ padding: '12px' }}>{(run.report.score_bps / 100).toFixed(2)}%</td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          color: run.report.band === "LOW" ? '#4ade80' : 
                                 run.report.band === "MEDIUM" ? '#facc15' : 
                                 run.report.band === "HIGH" ? '#fb923c' : '#f87171'
                        }}>
                          {run.report.band}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <a 
                          href={run.casper.explorer_hint} 
                          target="_blank" 
                          rel="noreferrer"
                          style={{ color: '#60a5fa', textDecoration: 'underline' }}
                        >
                          {run.casper.deploy_hash.substring(0, 16)}...
                        </a>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          fontSize: '11px',
                          padding: '2px 6px',
                          borderRadius: '6px',
                          background: (run.casper.mode === 'real' || run.casper.mode === 'testnet') ? 'rgba(34,197,94,0.1)' : 'rgba(255,255,255,0.05)',
                          color: (run.casper.mode === 'real' || run.casper.mode === 'testnet') ? '#4ade80' : '#94a3b8'
                        }}>
                          {run.casper.mode}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="card wide">
          <h2>Why Casper for RWA?</h2>
          <p style={{ margin: '0', color: '#cbd5e1', lineHeight: '1.6' }}>
            Lending protocols and yield aggregators need up-to-date, verifiable risk metrics. Storing private or bulky invoice data on-chain is expensive and unsecure. With Casper, our agent publishes compact, cryptographic evidence hashes on-chain, proving exactly when and why risk changed, while private details remain stored in secure data directories or behind paid gateways.
          </p>
        </div>
      </section>
    </main>
  );
}
