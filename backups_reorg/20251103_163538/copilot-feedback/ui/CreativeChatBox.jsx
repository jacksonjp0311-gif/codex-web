import React, { useState } from "react";

export default function CreativeChatBox({ context, onRequest }) {
  const [prompt, setPrompt] = useState("");
  return (
    <div>
      <textarea 
        placeholder="Describe the change…" 
        onChange={e=>setPrompt(e.target.value)} 
        value={prompt}
      />
      <button onClick={()=>{ 
        onRequest({ context, prompt, parallel: 5 }); 
        setPrompt(""); 
      }}>
        Patch
      </button>
    </div>
  );
}
