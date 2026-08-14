import type {
  DailyVolume,
  MetricsSummary,
  TopAddress,
  TopAddressSort,
} from "../types/metrics";

export async function getMetricsSummary(): Promise<MetricsSummary> {
  const response = await fetch("/api/metrics/summary");

  if (!response.ok) {
    throw new Error("Failed to load summary metrics");
  }

  return response.json();
}

export async function getDailyVolume(
  days = 30,
): Promise<DailyVolume[]> {
  const response = await fetch(
    `/api/metrics/volume?days=${days}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load daily volume");
  }

  return response.json();
}

export async function getTopAddresses(
  limit = 10,
  sortBy: TopAddressSort = "volume",
): Promise<TopAddress[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    sort_by: sortBy,
  });

  const response = await fetch(
    `/api/metrics/top-addresses?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load top addresses");
  }

  return response.json();
}