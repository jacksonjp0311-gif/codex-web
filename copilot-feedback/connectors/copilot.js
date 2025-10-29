module.exports = {
  execute: async ({ args }) => ({
    success: true,
    outputs: { patches: ["patch1","patch2"] },
    logs: ["stubbed copilot"]
  })
};
