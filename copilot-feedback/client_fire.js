# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
const io = require("socket.io-client");
const sock = io("http://localhost:4000", { reconnectionDelayMax: 1000 });
sock.on("connect", () => {
  console.log("CLIENT CONNECTED", sock.id);
  sock.emit("runSmartCycle");
  // wait for any smartCycleComplete then exit
  sock.once("smartCycleComplete", (results) => {
    console.log("CLIENT RECEIVED smartCycleComplete", JSON.stringify(results));
    setTimeout(()=> process.exit(0), 200);
  });
  // safety exit if nothing returns in 5s
  setTimeout(()=> process.exit(0), 5000);
});
sock.on("connect_error", (e) => { console.error("CONNECT_ERROR", e && e.message); setTimeout(()=> process.exit(1),200); });

