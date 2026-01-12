const { version } = require("./package.json");

function printVersion() {
  console.log(version);
  process.exit(0);
}

printVersion();
