import React, { useState, useEffect } from "react";
import { socket } from "./socket";
export default function ApprovalTab() {
  const [paths, setPaths] = useState([]);
  useEffect(() => {
    socket.on("suggestions", ({ paths }) => setPaths(paths));
    return () => socket.off("suggestions");
  }, []);
  return (
    <div style={{ padding:"1rem", background:"#111", color:"#79c0ff" }}>
      <h2>Path Suggestions</h2>
      {paths.map(p=>(
        <div key={p.path} style={{ margin:"0.5rem 0" }}>
          <strong>{p.path}</strong> — {p.description}
          <button onClick={()=>socket.emit("approvePath",{path:p.path})}
                  style={{
                    marginLeft:"1rem", background:"#79c0ff",
                    color:"#000", border:"none", padding:"0.25rem 0.5rem",
                    borderRadius:"0.25rem"
                  }}>
            Approve
          </button>
        </div>
      ))}
    </div>
  );
}
