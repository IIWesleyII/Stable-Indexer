import type {
  MetricsNetwork,
  TopAddressSort,
} from "../types/metrics";

export function buildMetricsSummaryUrl(
  chain: MetricsNetwork,
): string {
  const params = new URLSearchParams({
    chain,
  });

  return `/api/metrics/summary?${params}`;
}

export function buildDailyVolumeUrl(
  chain: MetricsNetwork,
  days = 30,
): string {
  const params = new URLSearchParams({
    days: String(days),
    chain,
  });

  return `/api/metrics/volume?${params}`;
}

export function buildTopAddressesUrl(
  chain: MetricsNetwork,
  limit = 10,
  sortBy: TopAddressSort = "volume",
): string {
  const params = new URLSearchParams({
    limit: String(limit),
    sort_by: sortBy,
    chain,
  });

  return `/api/metrics/top-addresses?${params}`;
}
