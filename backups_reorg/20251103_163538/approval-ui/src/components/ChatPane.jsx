import React, { useState, useEffect } from "react";
import io from "socket.io-client";

export default function ChatPane() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const sock = io("http://localhost:4000");
    ["suggestions","approvePath","callbackInvoked"].forEach(evt =>
      sock.on(evt, payload =>
        setLogs(prev => [...prev, `【${evt.toUpperCase()}】 ${JSON.stringify(payload)}`])
      )
    );
    return () => sock.disconnect();
  }, []);

  return (
    <div style={{
      backgroundColor: "#111",
      border: "1px solid #36fffb",
      borderRadius: "8px",
      padding: "1rem",
      maxHeight: "50vh",
      overflowY: "auto"
    }}>
      <h2 style={{ color: "#36fffb" }}>Live Logs</h2>
      <pre style={{
        color: "#36fffb",
        whiteSpace: "pre-wrap",
        fontFamily: "'Orbitron', monospace"
      }}>
        {logs.join("\n")}
      </pre>
    </div>
  );
}