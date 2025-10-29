(async function(){
  try {
    const io = require("socket.io-client");
    const inspect = (o)=>{ try { return JSON.stringify(o,null,2) } catch(e){ return String(o) } };
    const s = io("http://localhost:4000", { transports: ["polling","websocket"], reconnectionDelayMax: 2000 });
    s.on("connect", ()=>{ console.log("EMITTER connected", {id: s.id}); s.emit("runSmartCycle"); });
    s.on("connect_error", (e)=>{ console.error("EMITTER connect_error", (e && (e.message||e))); });
    s.on("disconnect", (r)=>{ console.log("EMITTER disconnect", r); });
    s.on("suggestions", (d)=>{ console.log("EMITTER suggestions", inspect(d)); });
    s.on("smartCycleComplete", (r)=>{ console.log("EMITTER smartCycleComplete", inspect(r)); });
    // keep alive briefly to collect events
    setTimeout(()=>{ try{ s.close(); }catch(e){}; process.exit(0); }, 12000);
  } catch(e) {
    console.error("EMITTER error", e && (e.message||e));
    process.exit(1);
  }
})();
