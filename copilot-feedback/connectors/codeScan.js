module.exports = {
  execute: async ({ args }) => ({
    success: true,
    outputs: { reportPath: "report.json" },
    logs: ["stubbed codeScan"]
  })
};
