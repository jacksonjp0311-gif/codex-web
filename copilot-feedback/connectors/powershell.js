module.exports = {
  execute: async ({ command }) => ({
    success: true,
    outputs: { stdout: `stubbed powershell: ${command}`, stderr: "" },
    logs: [`stubbed powershell: ${command}`]
  })
};
