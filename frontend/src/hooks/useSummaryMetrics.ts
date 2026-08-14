import { useEffect, useState } from "react";

import { getMetricsSummary } from "../api/metrics";
import type { MetricsSummary } from "../types/metrics";

export function useSummaryMetrics() {
  const [data, setData] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const metrics = await getMetricsSummary();

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
  }, []);

  return {
    data,
    loading,
    error,
  };
}