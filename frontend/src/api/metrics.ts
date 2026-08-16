import type {
  DailyVolume,
  MetricsNetwork,
  MetricsSummary,
  TopAddress,
  TopAddressSort,
} from "../types/metrics";
import {
  buildDailyVolumeUrl,
  buildMetricsSummaryUrl,
  buildTopAddressesUrl,
} from "./metricsUrls";

export async function getMetricsSummary(
  chain: MetricsNetwork,
): Promise<MetricsSummary> {
  const response = await fetch(
    buildMetricsSummaryUrl(chain),
  );

  if (!response.ok) {
    throw new Error("Failed to load summary metrics");
  }

  return response.json();
}

export async function getDailyVolume(
  chain: MetricsNetwork,
  days = 30,
): Promise<DailyVolume[]> {
  const response = await fetch(
    buildDailyVolumeUrl(
      chain,
      days,
    ),
  );

  if (!response.ok) {
    throw new Error("Failed to load daily volume");
  }

  return response.json();
}

export async function getTopAddresses(
  chain: MetricsNetwork,
  limit = 10,
  sortBy: TopAddressSort = "volume",
): Promise<TopAddress[]> {
  const response = await fetch(
    buildTopAddressesUrl(
      chain,
      limit,
      sortBy,
    ),
  );

  if (!response.ok) {
    throw new Error("Failed to load top addresses");
  }

  return response.json();
}
