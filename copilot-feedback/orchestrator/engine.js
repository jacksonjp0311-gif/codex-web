const fs    = require("fs")
const YAML  = require("yaml")
const EventBus = require("../orchestrator/eventBus")

class Engine {
  constructor() { this.connectors = {} }
  register(name, mod) { this.connectors[name] = mod }
  async run(workflowPath, payload = {}) {
    const wf = YAML.parse(fs.readFileSync(workflowPath, "utf-8"))
    for (const step of wf.steps) {
      const mod = this.connectors[step.node]
      const args = JSON.parse(JSON.stringify(step.args), (k,v)=>
        typeof v=="string" && v.match(/{{.*}}/) 
          ? payload[v.replace(/{{|}}/g, "").split('.')[1]] 
          : v
      )
      const res = await mod.execute(args)
      payload[step.name] = res.outputs || {}
      EventBus.emit("step", { name: step.name, logs: res.logs })
    }
    return payload
  }
}

module.exports = Engine
