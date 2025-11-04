import React, { useState, useEffect } from "react";
import io from "socket.io-client";

export default function ApprovalTab() {
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const sock = io("http://localhost:4000");
    sock.on("suggestions", data => {
      setOptions(data.paths || []);
      setSelected(null);
    });
    return () => sock.disconnect();
  }, []);

  const approve = () => {
    if (!selected) return;
    io("http://localhost:4000").emit("approvePath", { path: selected.path });
  };

  return (
    <div style={{ marginBottom: "1rem" }}>
      <h2>Path Suggestions</h2>
      <ul>
        {options.map(opt => (
          <li key={opt.path} style={{ margin: "0.5rem 0" }}>
            <label style={{ cursor: "pointer" }}>
              <input
                type="radio"
                name="path"
                checked={selected?.path === opt.path}
                onChange={() => setSelected(opt)}
                style={{ marginRight: "0.5rem" }}
              />
              <strong>{opt.path}</strong> — {opt.description}
            </label>
          </li>
        ))}
      </ul>
      <button
        onClick={approve}
        disabled={!selected}
        style={{
          background: selected ? "#36fffb" : "#444",
          color: "#0a0a0a",
          padding: "0.5rem 1rem",
          border: "none",
          borderRadius: "4px",
          cursor: selected ? "pointer" : "not-allowed"
        }}
      >
        Approve
      </button>
    </div>
  );
}