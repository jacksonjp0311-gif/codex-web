import React, { useState } from "react";
import Header      from "./Header";
import ApprovalTab from "./ApprovalTab";
import LiveLogs    from "./LiveLogs";
import ChatPane    from "./ChatPane";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100vh" }}>
      <Header onToggle={()=>setChatOpen(o=>!o)} open={chatOpen} />
      <div style={{ display:"flex", flex:1 }}>
        <div style={{ flex:2, display:"flex", flexDirection:"column" }}>
          <ApprovalTab />
          <LiveLogs style={{ flex:1, marginTop:"1rem" }} />
        </div>
        {chatOpen && <div style={{ flex:1, borderLeft:"1px solid #444" }}>
          <ChatPane />
        </div>}
      </div>
    </div>
  );
}
