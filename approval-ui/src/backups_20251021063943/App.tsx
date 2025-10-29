import React from "react";
import { ChatPane } from "./components/ChatPane";
import { ApprovalTab } from "./components/ApprovalTab";

function App() {
  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h1>Feedback-Loop UI</h1>
      <ApprovalTab />
      <hr />
      <ChatPane />
    </div>
  );
}

export default App;
