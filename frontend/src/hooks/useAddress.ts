import { useEffect, useState } from "react";

import { getAddressSummary } from "../api/addresses";
import type { AddressSummary } from "../types/addresses";
import type { MetricsNetwork } from "../types/metrics";


export function useAddress(
  address: string | undefined,
  chain: MetricsNetwork,
) {
  const [data, setData] =
    useState<AddressSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    if (!address) {
      setLoading(false);
      setError("Address is missing");
      return;
    }

    async function loadAddress() {
      try {
        setLoading(true);
        setError(null);

        const result = await getAddressSummary(
          address!,
          chain,
        );

        setData(result);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(
            "Failed to load address",
          );
        }
      } finally {
        setLoading(false);
      }
    }

    loadAddress();
  }, [address, chain]);

  return {
    data,
    loading,
    error,
  };
}
