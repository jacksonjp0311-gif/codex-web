# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
const ioClient = require("socket.io-client");
const socket   = ioClient("http://localhost:4000");

socket.on("connect", () => console.log("🔌 Test client connected"));

socket.on("suggestions", ({ suggestions }) => {
  console.log("📨 Received suggestions:", { patches: suggestions });
  socket.emit("approvedPatches", { patches: suggestions });
});

socket.on("step", ({ name }) =>
  console.log(`» Step ${name}`)
);
socket.on("log", ({ step, message }) =>
  console.log(`   - [${step}] ${message}`)
);
socket.on("error", ({ message }) => {
  console.error("❌ Workflow error:", message);
  process.exit(1);
});
socket.on("done", payload => {
  console.log("🎉 Workflow complete", payload);
  process.exit(0);
});

