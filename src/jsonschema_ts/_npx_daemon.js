const { createRequire } = require("module");
const path = require("path");
const os = require("os");
const readline = require("readline");

let compile;

function loadCompile() {
  try {
    compile = require("json-schema-to-typescript").compile;
    return;
  } catch {
    const nodePath =
      process.env.JSONSCHEMA_TS_CACHE ||
      path.join(os.homedir(), ".jsonschema-ts", "node_modules");
    const pkgPath = path.join(
      nodePath,
      "json-schema-to-typescript",
      "package.json"
    );
    try {
      const localRequire = createRequire(pkgPath);
      compile = localRequire("json-schema-to-typescript").compile;
    } catch {
      process.stderr.write(
        JSON.stringify({
          success: false,
          error: "Cannot find json-schema-to-typescript module",
        }) + "\n"
      );
      process.exit(1);
    }
  }
}

loadCompile();

const rl = readline.createInterface({ input: process.stdin });

let queue = [];
let processing = false;

function processNext() {
  if (processing || queue.length === 0) return;
  processing = true;
  const { schema, options, resolve, reject } = queue.shift();

  const title = schema.title || "Root";
  compile(schema, title, options)
    .then((ts) => {
      process.stdout.write(
        JSON.stringify({ success: true, data: ts }) + "\n"
      );
      resolve();
    })
    .catch((err) => {
      process.stdout.write(
        JSON.stringify({ success: false, error: err.message }) + "\n"
      );
      reject();
    })
    .finally(() => {
      processing = false;
      processNext();
    });
}

rl.on("line", (line) => {
  line = line.trim();
  if (!line) return;
  try {
    const msg = JSON.parse(line);
    new Promise((resolve, reject) => {
      queue.push({
        schema: msg.schema,
        options: msg.options || {},
        resolve,
        reject,
      });
      processNext();
    });
  } catch (err) {
    process.stdout.write(
      JSON.stringify({ success: false, error: "Invalid JSON: " + err.message }) +
        "\n"
    );
  }
});

rl.on("close", () => {
  process.exit(0);
});

process.on("SIGTERM", () => {
  process.exit(0);
});
