#!/usr/bin/env node
/**
 * Append an intentional lint violation to the supplied TypeScript module.
 */

const fs = require("fs");
const path = require("path");

const [, , targetPathArg] = process.argv;

if (!targetPathArg) {
  throw new Error("A target file path must be provided.");
}

const targetPath = path.resolve(targetPathArg);
if (!fs.existsSync(targetPath)) {
  throw new Error(`Cannot introduce lint failure into missing file: ${targetPath}`);
}

const marker = "// META_LINT_FAILURE";
const snippet = `\n${marker}\nconst unusedMetaLintVariable = 42;\n`;

const contents = fs.readFileSync(targetPath, "utf8");
if (contents.includes(marker)) {
  // Allow repeated executions without duplicating the failure.
  process.exit(0);
}

fs.writeFileSync(targetPath, `${contents.trimEnd()}${snippet}`);
