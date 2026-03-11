import { useState, useRef } from "react";
import { api } from "../api/client";

export default function InputPanel({ onResult, loading, setLoading }) {
  const [tab, setTab] = useState("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const handle = async (fn) => {
    setError("");
    setLoading(true);
    try {
      const result = await fn();
      onResult(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const submitText = () => {
    if (text.trim().length < 50) { setError("Please enter at least 50 characters."); return; }
    handle(() => api.summariseText(text.trim()));
  };

  const submitUrl = () => {
    if (!url.trim()) { setError("Enter a URL."); return; }
    handle(() => api.summariseUrl(url.trim()));
  };

  const submitFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    handle(() => api.summariseFile(file));
  };

  return (
    <div className="input-panel">
      <div className="input-tabs">
        {["text", "url", "file"].map(t => (
          <button
            key={t}
            className={`input-tab ${tab === t ? "active" : ""}`}
            onClick={() => { setTab(t); setError(""); }}
          >
            {t === "text" ? "Text" : t === "url" ? "URL" : "File"}
          </button>
        ))}
      </div>

      {tab === "text" && (
        <div className="input-body">
          <textarea
            className="text-input"
            placeholder="Paste your document text here…"
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <div className="input-footer">
            <span className="char-count">{text.length.toLocaleString()} chars</span>
            <button className="btn-primary" onClick={submitText} disabled={loading}>
              {loading ? "Summarising…" : "Summarise →"}
            </button>
          </div>
        </div>
      )}

      {tab === "url" && (
        <div className="input-body">
          <input
            className="url-input"
            placeholder="https://example.com/article"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && submitUrl()}
            inputMode="url"
            autoCapitalize="none"
            autoCorrect="off"
          />
          <p className="input-hint">Paste any article or web page URL. Text will be extracted automatically.</p>
          <div className="input-footer">
            <span />
            <button className="btn-primary" onClick={submitUrl} disabled={loading}>
              {loading ? "Fetching…" : "Fetch & Summarise →"}
            </button>
          </div>
        </div>
      )}

      {tab === "file" && (
        <div className="input-body">
          <div
            className="file-drop"
            onClick={() => fileRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f) {
                const dt = new DataTransfer();
                dt.items.add(f);
                fileRef.current.files = dt.files;
                submitFile({ target: fileRef.current });
              }
            }}
          >
            <div className="file-drop-icon">⬆</div>
            <p>Tap to upload a PDF or DOCX</p>
            <p className="input-hint">or drag and drop on desktop</p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx"
            style={{ display: "none" }}
            onChange={submitFile}
          />
        </div>
      )}

      {error && <p className="input-error">{error}</p>}
    </div>
  );
}
