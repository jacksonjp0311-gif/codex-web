const EventBus = require("../orchestrator/eventBus");

module.exports = {
  execute: async ({ suggestions }) => {
    // broadcast suggestions to any connected UI
    global._io.emit("suggestions", { suggestions });

    // wait for the user's approval response
    const approvedPatches = await new Promise(resolve => {
      EventBus.once("user-approval-response", ({ patches }) => {
        resolve(patches);
      });
    });

    return {
      success: true,
      outputs: { approvedPatches },
      logs: ["user approved patches"]
    };
  }
};
