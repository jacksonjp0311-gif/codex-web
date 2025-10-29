import React from "react";
export default function Header({ onToggle, open }) {
  return (
    <div style={{ padding:"0.5rem", background:"#222", color:"#79c0ff", display:"flex", justifyContent:"space-between" }}>
      <h1 style={{ margin:0 }}>Feedback Loop UI</h1>
      <button
        onClick={onToggle}
        style={{
          background: open ? "#444" : "#79c0ff",
          color: open ? "#79c0ff" : "#000",
          border:"none", padding:"0.5rem", borderRadius:"0.25rem"
        }}
      >
        Copilot
      </button>
    </div>
  );
}
