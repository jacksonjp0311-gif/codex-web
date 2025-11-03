import React, { useState, useEffect } from "react";
import { socket } from "./socket";
export default function LiveLogs({ style }) {
  const [events, setE] = useState([]);
  useEffect(()=>{
    const h={ 
      suggestions:d=>setE(e=>[...e,`[SUGGESTIONS] ${JSON.stringify(d)}`]),
      approvePath:d=>setE(e=>[...e,`[APPROVEPATH] ${JSON.stringify(d)}`]),
      callbackInvoked:d=>setE(e=>[...e,`[CALLBACK] ${JSON.stringify(d)}`])
    };
    Object.entries(h).forEach(([ev,fn])=>socket.on(ev,fn));
    return ()=>Object.entries(h).forEach(([ev,fn])=>socket.off(ev,fn));
  },[]);
  return (
    <div style={{
      padding:"1rem", background:"#000", color:"#79c0ff",
      fontFamily:"monospace", overflowY:"auto", ...style
    }}>
      <h3>Live Logs</h3>
      {events.map((l,i)=><div key={i}>{l}</div>)}
    </div>
  );
}
