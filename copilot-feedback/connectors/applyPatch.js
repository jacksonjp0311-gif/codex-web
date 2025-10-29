module.exports = {
  execute: async ({ args }) => ({
    success: true,
    outputs: { applied: true },
    logs: ["stubbed applyPatch"]
  })
};
