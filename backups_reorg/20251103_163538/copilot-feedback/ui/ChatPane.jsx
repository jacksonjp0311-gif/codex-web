import React, { useState } from "react";

export default function ChatPane({ messages, onSend }) {
  const [text, setText] = useState("");
  return (
    <div>
      {messages.map((m,i)=><div key={i}>{m.content}</div>)}
      <textarea onChange={e=>setText(e.target.value)} value={text}/>
      <button onClick={()=>{ onSend(text); setText(""); }}>Send</button>
    </div>
  );
}
