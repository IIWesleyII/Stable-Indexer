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

const dailyActivity = await importTypeScript(
  "src/lib/dailyActivity.ts",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("base"),
  "/api/metrics/summary?chain=base",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("ethereum"),
  "/api/metrics/summary?chain=ethereum",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("solana"),
  "/api/metrics/summary?chain=solana",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("tron"),
  "/api/metrics/summary?chain=tron",
);

assert.equal(
  metricsUrls.buildMetricsSummaryUrl("all"),
  "/api/metrics/summary",
);

assert.equal(
  metricsUrls.buildDailyVolumeUrl("all", 14),
  "/api/metrics/volume?days=14",
);

assert.equal(
  metricsUrls.buildTopAddressesUrl("all", 25, "volume"),
  "/api/metrics/top-addresses?limit=25&sort_by=volume",
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
      label: "Ethereum",
      value: "ethereum",
    },
    {
      label: "Solana",
      value: "solana",
    },
    {
      label: "Tron",
      value: "tron",
    },
  ],
);

assert.equal(
  networks.parseMetricsNetwork(null),
  "base",
);

assert.equal(
  networks.parseDashboardNetwork("all"),
  "all",
);

assert.equal(
  networks.getDashboardNetworkLabel("all"),
  "All Networks",
);

assert.equal(
  networks.parseMetricsNetwork("ethereum"),
  "ethereum",
);

assert.equal(
  networks.parseMetricsNetwork("solana"),
  "solana",
);

assert.equal(
  networks.parseMetricsNetwork("tron"),
  "tron",
);

assert.deepEqual(
  dailyActivity.buildDailyActivityChartData([
    {
      date: "2026-08-18",
      token_symbol: "USDC",
      transfer_count: 12,
      volume: "1250.50",
    },
    {
      date: "2026-08-18",
      token_symbol: "USDT",
      transfer_count: 8,
      volume: "900.25",
    },
    {
      date: "2026-08-19",
      token_symbol: "USDC",
      transfer_count: 4,
      volume: "75.00",
    },
  ]),
  [
    {
      date: "2026-08-18",
      usdc_volume: 1250.5,
      usdc_transfer_count: 12,
      usdt_volume: 900.25,
      usdt_transfer_count: 8,
    },
    {
      date: "2026-08-19",
      usdc_volume: 75,
      usdc_transfer_count: 4,
      usdt_volume: 0,
      usdt_transfer_count: 0,
    },
  ],
);

console.log("Regression checks passed");
