import React, { useEffect, useState } from "react";

export default function App() {
  const [smartResult, setSmartResult] = useState(null);
  const [smartSuggestions, setSmartSuggestions] = useState([]);
  const [runningSmart, setRunningSmart] = useState(false);

  function emitRunSmartCycle() {
    try {
      setRunningSmart(true);
      const s = window.socket;
      if (!s || !s.emit) { setRunningSmart(false); return; }
      s.emit("runSmartCycle");
    } catch (e) { console.error("emit error", e); setRunningSmart(false); }
  }

  useEffect(() => {
    const s = window.socket;
    if (!s) return;
    const onSmart = (payload) => { setSmartResult(payload); setRunningSmart(false); };
    const onSug = (data) => { const arr = Array.isArray(data.paths) ? data.paths : (data.paths || []); setSmartSuggestions(arr); };
    s.on && s.on("smartCycleComplete", onSmart);
    s.on && s.on("suggestions", onSug);
    return () => { s.off && s.off("smartCycleComplete", onSmart); s.off && s.off("suggestions", onSug); };
  }, []);

  return (
    <div style={{ padding: 16, fontFamily: "sans-serif" }}>
      <h2>Approval UI</h2>
      <div style={{ marginBottom: 12, display: "flex", gap: 8, alignItems: "center" }}>
        <button onClick={emitRunSmartCycle} disabled={runningSmart} style={{ padding: "8px 12px", background: "#0b5fff", color: "white", border: "none", borderRadius: 4 }}>
          {runningSmart ? "Running..." : "Run Smart Cycle"}
        </button>
        <div style={{ fontSize: 12, color: "#666" }}><strong>Smart</strong> results panel</div>
      </div>
      <div style={{ border: "1px solid #eee", padding: 10, borderRadius: 6, background: "#fafafa", maxHeight: 320, overflow: "auto" }}>
        <div style={{ marginBottom: 8 }}><strong>Last smartCycleComplete</strong></div>
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>{smartResult ? JSON.stringify(smartResult, null, 2) : "No results yet"}</pre>
        <div style={{ marginTop: 8 }}><strong>Latest suggestions</strong></div>
        <ul>{smartSuggestions && smartSuggestions.length ? smartSuggestions.map((p,i)=>(<li key={i}><strong>{p.path}</strong>: {p.description}</li>)) : <li>None</li>}</ul>
      </div>
    </div>
  );
}

