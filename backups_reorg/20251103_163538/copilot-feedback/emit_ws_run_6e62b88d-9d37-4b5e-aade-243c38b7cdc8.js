# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
(async function(){
  try {
    const io = require("socket.io-client");
    const inspect = (o)=>{ try { return JSON.stringify(o) } catch(e){ return String(o) } };
    const s = io("ws://127.0.0.1:4000", { transports: ["websocket"], reconnection: false, timeout: 5000 });
    s.on("connect", ()=>{ console.log("EMITTER connected", s.id); s.emit("runSmartCycle"); });
    s.on("connect_error",(e)=>{ console.error("EMITTER connect_error", e && (e.message||e)); });
    s.on("suggestions",(d)=>{ console.log("EMITTER suggestions", inspect(d)); });
    s.on("smartCycleComplete",(r)=>{ console.log("EMITTER smartCycleComplete", inspect(r)); });
    setTimeout(()=>{ try{ s.close(); }catch(e){}; process.exit(0); }, 8000);
  } catch(e) { console.error("EMITTER error", e && (e.message||e)); process.exit(1); }
})();

