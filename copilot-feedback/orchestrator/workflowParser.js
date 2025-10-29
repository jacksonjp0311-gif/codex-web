const fs   = require("fs")
const YAML = require("yaml")

module.exports = {
  parse: (filePath) => YAML.parse(fs.readFileSync(filePath, "utf-8"))
}
