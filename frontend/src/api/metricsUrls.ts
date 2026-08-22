import type {
  DashboardNetwork,
  TopAddressSort,
} from "../types/metrics";

function buildMetricUrl(
  path: string,
  params: URLSearchParams,
): string {
  return params.size > 0 ? `${path}?${params}` : path;
}

export function buildMetricsSummaryUrl(
  chain: DashboardNetwork,
): string {
  const params = new URLSearchParams();

  if (chain !== "all") {
    params.set("chain", chain);
  }

  return buildMetricUrl("/api/metrics/summary", params);
}

export function buildDailyVolumeUrl(
  chain: DashboardNetwork,
  days = 30,
): string {
  const params = new URLSearchParams({
    days: String(days),
  });

  if (chain !== "all") {
    params.set("chain", chain);
  }

  return buildMetricUrl("/api/metrics/volume", params);
}

export function buildTopAddressesUrl(
  chain: DashboardNetwork,
  limit = 10,
  sortBy: TopAddressSort = "volume",
): string {
  const params = new URLSearchParams({
    limit: String(limit),
    sort_by: sortBy,
  });

  if (chain !== "all") {
    params.set("chain", chain);
  }

  return buildMetricUrl("/api/metrics/top-addresses", params);
}
