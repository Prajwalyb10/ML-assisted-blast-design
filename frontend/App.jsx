import { useEffect, useState } from "react";
import Form from "./Form";
import Plot from "./Plot";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const PATTERN_LABELS = {
  square: "Square",
  staggered: "Staggered",
  rectangular: "Rectangular",
  v_pattern: "V-Pattern",
  diagonal: "Diagonal",
  line_drilling: "Line Drilling",
  fan: "Fan",
};

const PREDICTION_LABELS = {
  burden: "Burden (m)",
  spacing: "Spacing (m)",
  charge_per_hole: "Charge/Hole (kg)",
  stemming_length: "Stemming (m)",
  sub_drilling: "Sub Drill (m)",
  flyrock_distance: "Flyrock (m)",
};

export default function App() {
  const [loading, setLoading] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState(null);
  const [design, setDesign] = useState(null);
  const [referenceData, setReferenceData] = useState(null);

  useEffect(() => {
    async function loadReferenceData() {
      try {
        const res = await fetch(`${API_BASE}/reference-data`);
        if (!res.ok) {
          throw new Error(`Failed to load reference data (${res.status})`);
        }
        const data = await res.json();
        setReferenceData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setBootLoading(false);
      }
    }

    loadReferenceData();
  }, []);

  async function handleGenerate(params) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/generate-pattern`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      setDesign(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleExport() {
    if (!design) return;
    const blob = new Blob([JSON.stringify(design, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `blast_design_${Date.now()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-logo">BD</div>
        <div>
          <h1>Blast Design Dashboard</h1>
          <p>ML-backed blast geometry, pattern selection, and layout generation</p>
        </div>
        <span className="header-tag">Dataset-ready</span>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <Form
            onGenerate={handleGenerate}
            loading={loading}
            referenceData={referenceData}
            bootLoading={bootLoading}
          />

          {error && (
            <div className="error-banner">
              <strong>Error:</strong> {error}
            </div>
          )}

          {referenceData && (
            <div className="stats-card">
              <div className="stats-title">Model Health</div>
              <div className="mini-note">Using {referenceData.selected_features.length} selected ML features.</div>
              <div className="stats-grid compact-grid">
                {Object.entries(referenceData.model_metrics).map(([key, metric]) => (
                  <div key={key} className="stat-cell">
                    <div className="stat-label">{PREDICTION_LABELS[key] || key}</div>
                    <div className="stat-value">R2 {metric.r2}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {design && (
            <div className="stats-card">
              <div className="stats-title">Recommended Design</div>
              <div className="pattern-badge">
                <span className="dot" />
                {PATTERN_LABELS[design.pattern] || design.pattern}
              </div>
              <div className="ai-reason">
                {(design.ai_selected ? "AI selected" : "Manual override") + ": " + design.ai_reasons.join(" | ")}
              </div>

              <div className="subsection-title">Predicted Outputs</div>
              <div className="stats-grid compact-grid">
                {Object.entries(design.predictions).map(([key, value]) => (
                  <div key={key} className="stat-cell">
                    <div className="stat-label">{PREDICTION_LABELS[key] || key}</div>
                    <div className="stat-value">{value}</div>
                  </div>
                ))}
              </div>

              <div className="subsection-title">Blast Metrics</div>
              <div className="stats-grid compact-grid">
                {[
                  ["Total Holes", design.metadata.total_holes],
                  ["Rows", design.metadata.rows],
                  ["S/B Ratio", design.metadata.spacing_burden_ratio],
                  ["Area (m2)", design.metadata.blast_area_m2],
                  ["Volume (m3)", design.metadata.blasted_volume_m3],
                  ["Charge/Hole", design.metadata.charge_per_hole_kg],
                  ["Explosive (kg)", design.metadata.total_explosive_kg],
                  ["Flyrock (m)", design.metadata.flyrock_distance_m],
                ].map(([label, value]) => (
                  <div key={label} className="stat-cell">
                    <div className="stat-label">{label}</div>
                    <div className="stat-value">{value}</div>
                  </div>
                ))}
              </div>

              <div className="mini-note">
                Rock: {design.input_summary.rock_type_label} ({design.input_summary.rock_category}) | Explosive: {design.input_summary.explosive_type_label}
              </div>

              <button className="btn-export" onClick={handleExport}>
                Export JSON
              </button>
            </div>
          )}
        </aside>

        <main className="canvas-area">
          {loading && (
            <div className="loading-overlay">
              <div className="spinner" />
              <span>Generating blast design...</span>
            </div>
          )}

          {!loading && design ? (
            <Plot design={design} />
          ) : !loading ? (
            <div className="empty-state">
              <div className="empty-icon">GRID</div>
              <p>Enter blast inputs and generate a machine-learned design.</p>
              <p className="empty-sub">The backend predicts geometry, explosive loading, and flyrock, then draws the pattern.</p>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}
