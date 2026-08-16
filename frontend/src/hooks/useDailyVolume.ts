import { useEffect, useState } from "react";

import { getDailyVolume } from "../api/metrics";
import type {
  DailyVolume,
  MetricsNetwork,
} from "../types/metrics";

export function useDailyVolume(
  chain: MetricsNetwork,
  days = 30,
) {
  const [data, setData] = useState<DailyVolume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadVolume() {
      try {
        setLoading(true);
        setError(null);

        const volume = await getDailyVolume(
          chain,
          days,
        );

        setData(volume);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load daily volume");
        }
      } finally {
        setLoading(false);
      }
    }

    loadVolume();
  }, [chain, days]);

  return {
    data,
    loading,
    error,
  };
}
