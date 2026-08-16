import { useEffect, useState } from "react";

import { getMetricsSummary } from "../api/metrics";
import type {
  MetricsNetwork,
  MetricsSummary,
} from "../types/metrics";

export function useSummaryMetrics(chain: MetricsNetwork) {
  const [data, setData] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const metrics = await getMetricsSummary(chain);

        setData(metrics);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load metrics");
        }
      } finally {
        setLoading(false);
      }
    }

    loadMetrics();
  }, [chain]);

  return {
    data,
    loading,
    error,
  };
}
