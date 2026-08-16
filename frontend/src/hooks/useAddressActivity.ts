import { useEffect, useState } from "react";

import { getAddressActivity } from "../api/addresses";
import type { AddressActivity } from "../types/addresses";
import type { MetricsNetwork } from "../types/metrics";


export function useAddressActivity(
  address: string | undefined,
  chain: MetricsNetwork,
  limit = 20,
) {
  const [data, setData] = useState<AddressActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!address) {
      setLoading(false);
      return;
    }

    async function loadActivity() {
      try {
        setLoading(true);
        setError(null);

        const result = await getAddressActivity(
          address!,
          chain,
          limit,
        );

        setData(result);
      } catch (loadError) {
        if (loadError instanceof Error) {
          setError(loadError.message);
        } else {
          setError("Failed to load address activity");
        }
      } finally {
        setLoading(false);
      }
    }

    loadActivity();
  }, [address, chain, limit]);

  return {
    data,
    loading,
    error,
  };
}
