import React, { useState, useEffect, useRef } from "react";
import { socket } from "./socket";
export default function ChatPane() {
  const [msgs,set]=useState([]);
  const [draft,setDraft]=useState("");
  const endRef=useRef();
  useEffect(()=>{
    socket.on("chatResponse",({message})=>set(m=>[...m,{sender:"copilot",text:message}]));
    return ()=>socket.off("chatResponse");
  },[]);
  useEffect(()=>endRef.current?.scrollIntoView({behavior:"smooth"}),[msgs]);
  const send=()=>{
    if(!draft.trim())return;
    set(m=>[...m,{sender:"user",text:draft}]);
    socket.emit("chatMessage",{message:draft});
    setDraft("");
  };
  return (
    <div style={{display:"flex",flexDirection:"column",height:"100%",padding:"1rem"}}>
      <h3>Copilot Chat</h3>
      <div style={{flex:1,overflowY:"auto",marginBottom:"1rem"}}>
        {msgs.map((m,i)=>(
          <div key={i} style={{textAlign:m.sender==="user"?"right":"left",margin:"0.25rem 0"}}>
            <span style={{
              background:m.sender==="user"?"#79c0ff":"#444",color:"#fff",
              padding:"0.5rem",borderRadius:"0.5rem",display:"inline-block"
            }}>{m.text}</span>
          </div>
        ))}
        <div ref={endRef}/>
      </div>
      <div style={{display:"flex"}}>
        <input value={draft}
               onChange={e=>setDraft(e.target.value)}
               onKeyDown={e=>e.key==="Enter"&&send()}
               placeholder="Ask Copilot…"
               style={{
                 flex:1,padding:"0.5rem",marginRight:"0.5rem",
                 background:"#222",color:"#fff",border:"1px solid #444",
                 borderRadius:"0.25rem"
               }}/>
        <button onClick={send} style={{
          background:"#79c0ff",color:"#000",border:"none",padding:"0 1rem",borderRadius:"0.25rem"
        }}>Send</button>
      </div>
    </div>
  );
}
