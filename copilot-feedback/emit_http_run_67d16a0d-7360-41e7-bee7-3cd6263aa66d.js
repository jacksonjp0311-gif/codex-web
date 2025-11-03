# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
(async function(){
  try {
    const io = require("socket.io-client");
    const s = io("http://localhost:4000", { transports: ["polling","websocket"], reconnection: false, timeout: 12000, upgrade: true });
    s.on("connect", ()=>{ console.log("EMITTER connected", s.id); s.emit("runSmartCycle"); });
    s.on("connect_error",(e)=>{ console.error("EMITTER connect_error", e && (e.message||e)); });
    s.on("disconnect",(r)=>{ console.log("EMITTER disconnect", r); });
    s.on("suggestions",(d)=>{ console.log("EMITTER suggestions", JSON.stringify(d)); });
    s.on("smartCycleComplete",(r)=>{ console.log("EMITTER smartCycleComplete", JSON.stringify(r)); });
    setTimeout(()=>{ try{ s.close(); }catch(e){}; process.exit(0); }, 12000+4000);
  } catch(e) { console.error("EMITTER error", e && (e.message||e)); process.exit(1); }
})();

