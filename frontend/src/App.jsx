import { useState, useEffect } from "react";
import { api } from "./api/client";
import InputPanel from "./components/InputPanel";
import SaliencyView from "./components/SaliencyView";
import "./App.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const [view, setView] = useState("input"); // "input" | "result" | "history"
  const [stats, setStats] = useState({});

  useEffect(() => {
    api.listDocuments().then(setHistory).catch(() => {});
    api.getStats().then(setStats).catch(() => {});
  }, []);

  const handleResult = (res) => {
    setResult(res);
    setView("result");
    api.listDocuments().then(setHistory).catch(() => {});
    api.getStats().then(setStats).catch(() => {});
  };

  const loadDoc = async (id) => {
    try {
      const doc = await api.getDocument(id);
      setResult(doc);
      setView("result");
    } catch (e) { console.error(e); }
  };

  const deleteDoc = async (id, e) => {
    e.stopPropagation();
    await api.deleteDocument(id);
    setHistory(h => h.filter(d => d.id !== id));
    if (result?.id === id) { setResult(null); setView("input"); }
  };

  const topSentences = result?.sentences
    ? [...result.sentences].sort((a, b) => b.score - a.score).slice(0, 3)
    : [];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-mark">◈</span>
            <span className="logo-name">Saliency</span>
          </div>
          <span className="logo-sub">Document Summariser</span>
        </div>
        <div className="header-right">
          <span className="stat-pill">{stats.total_documents ?? 0} docs</span>
          <button className="btn-ghost sm" onClick={() => setView(v => v === "history" ? (result ? "result" : "input") : "history")}>
            {view === "history" ? "← Back" : "History"}
          </button>
        </div>
      </header>

      {/* Mobile nav tabs */}
      {view !== "history" && (
        <div className="mobile-nav">
          <button
            className={`mobile-tab ${view === "input" ? "active" : ""}`}
            onClick={() => setView("input")}
          >
            Input
          </button>
          <button
            className={`mobile-tab ${view === "result" ? "active" : ""}`}
            onClick={() => result && setView("result")}
            disabled={!result}
          >
            Result {result && <span className="result-dot" />}
          </button>
        </div>
      )}

      {/* Body */}
      <div className="body">

        {/* History */}
        {view === "history" && (
          <div className="history-panel">
            <h2>History</h2>
            {history.length === 0 && <p className="empty">No documents yet.</p>}
            <ul className="history-list">
              {history.map(doc => (
                <li key={doc.id} className="history-item" onClick={() => loadDoc(doc.id)}>
                  <div className="history-title">{doc.title || "Untitled"}</div>
                  <div className="history-meta">
                    <span className="source-badge">{doc.source_type}</span>
                    <span>{doc.word_count?.toLocaleString()} words</span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                  <button className="delete-btn" onClick={e => deleteDoc(doc.id, e)}>✕</button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Input view */}
        {view === "input" && (
          <div className="input-view">
            <InputPanel onResult={handleResult} loading={loading} setLoading={setLoading} />
          </div>
        )}

        {/* Result view */}
        {view === "result" && result && (
          <div className="result-view">
            {loading && (
              <div className="loading-state">
                <div className="spinner" />
                <p>Running T5 summarisation…</p>
                <p className="loading-sub">Extracting attention weights</p>
              </div>
            )}

            {!loading && (
              <div className="result">

                {/* Summary */}
                <div className="summary-card">
                  <div className="section-label">
                    Summary <span className="model-tag">flan-t5-base</span>
                  </div>
                  <p className="summary-text">{result.summary}</p>
                  <div className="summary-meta">
                    {result.word_count?.toLocaleString()} words · {result.sentences?.length} sentences analysed
                  </div>
                </div>

                {/* Key sentences */}
                {topSentences.length > 0 && (
                  <div className="key-sentences-card">
                    <div className="section-label">Highest attention sentences</div>
                    {topSentences.map(s => (
                      <div
                        key={s.index}
                        className="key-sentence"
                        onMouseEnter={() => setHoveredIdx(s.index)}
                        onMouseLeave={() => setHoveredIdx(null)}
                        onTouchStart={() => setHoveredIdx(s.index)}
                        onTouchEnd={() => setHoveredIdx(null)}
                      >
                        <div className="key-score-bar">
                          <div className="key-score-fill" style={{ width: `${s.score * 100}%` }} />
                        </div>
                        <p>{s.text.length > 140 ? s.text.slice(0, 138) + "…" : s.text}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Saliency legend */}
                <div className="legend">
                  <span className="legend-label">Attention</span>
                  <div className="legend-gradient" />
                  <span className="legend-lo">Low</span>
                  <span className="legend-hi">High</span>
                </div>

                {/* Original text with highlights */}
                <div className="section-label">
                  Original Text — tap sentences to inspect
                </div>
                <SaliencyView
                  sentences={result.sentences}
                  onHover={setHoveredIdx}
                  hoveredIdx={hoveredIdx}
                />

                {/* New document button */}
                <button className="btn-new" onClick={() => setView("input")}>
                  + Summarise another document
                </button>
              </div>
            )}
          </div>
        )}

        {/* Result placeholder when no result yet */}
        {view === "result" && !result && (
          <div className="empty-state">
            <div className="empty-mark">◈</div>
            <p>Submit a document to see the summary and saliency</p>
          </div>
        )}
      </div>
    </div>
  );
}
