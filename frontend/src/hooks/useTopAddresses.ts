import { useEffect, useState } from "react";

import { getTopAddresses } from "../api/metrics";
import type {
  MetricsNetwork,
  TopAddress,
  TopAddressSort,
} from "../types/metrics";

export function useTopAddresses(
  chain: MetricsNetwork,
  sortBy: TopAddressSort,
  limit = 10,
) {
  const [data, setData] = useState<TopAddress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAddresses() {
      try {
        setLoading(true);
        setError(null);

        const addresses = await getTopAddresses(
          chain,
          limit,
          sortBy,
        );

        setData(addresses);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load top addresses");
        }
      } finally {
        setLoading(false);
      }
    }

    loadAddresses();
  }, [chain, limit, sortBy]);

  return {
    data,
    loading,
    error,
  };
}
