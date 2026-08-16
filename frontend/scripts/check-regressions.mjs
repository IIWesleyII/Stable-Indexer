import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

import ts from "typescript";

const root = process.cwd();
const outDir = await mkdtemp(
  path.join(tmpdir(), "stable-indexer-tests-"),
);

async function importTypeScript(relativePath) {
  const sourcePath = path.join(root, relativePath);
  const source = await readFile(sourcePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2022,
      verbatimModuleSyntax: true,
    },
  });

  const outPath = path.join(
    outDir,
    relativePath.replace(/[\\/]/g, "_").replace(/\.ts$/, ".mjs"),
  );

  await writeFile(outPath, output.outputText);

  return import(pathToFileURL(outPath).href);
}

const metricsUrls = await importTypeScript(
  "src/api/metricsUrls.ts",
);

const networks = await importTypeScript(
  "src/lib/networks.ts",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("base"),
  "/api/metrics/summary?chain=base",
);

assert.equal(
  metricsUrls.buildDailyVolumeUrl("base-sepolia", 14),
  "/api/metrics/volume?days=14&chain=base-sepolia",
);

assert.equal(
  metricsUrls.buildTopAddressesUrl(
    "base",
    25,
    "transfer_count",
  ),
  "/api/metrics/top-addresses?limit=25&sort_by=transfer_count&chain=base",
);

assert.equal(
  networks.DEFAULT_METRICS_NETWORK,
  "base",
);

assert.deepEqual(
  networks.NETWORK_OPTIONS,
  [
    {
      label: "Base",
      value: "base",
    },
    {
      label: "Base Sepolia",
      value: "base-sepolia",
    },
  ],
);

assert.equal(
  networks.parseMetricsNetwork(null),
  "base",
);

assert.equal(
  networks.parseMetricsNetwork("base-sepolia"),
  "base-sepolia",
);

assert.equal(
  networks.parseMetricsNetwork("ethereum"),
  "base",
);

console.log("Regression checks passed");
