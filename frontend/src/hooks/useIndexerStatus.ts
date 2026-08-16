import { useEffect, useState } from "react";

import { getIndexerStatus } from "../api/indexer";
import type { IndexerStatus } from "../types/indexer";


const POLL_INTERVAL = 5000;


export function useIndexerStatus() {
  const [data, setData] = useState<IndexerStatus[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      try {
        const status = await getIndexerStatus();

        if (active) {
          setData(status);
          setError(null);
        }
      } catch (err) {
        if (!active) {
          return;
        }

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load indexer status");
        }
      }
    }

    loadStatus();

    const interval = window.setInterval(
      loadStatus,
      POLL_INTERVAL,
    );

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return {
    data,
    error,
  };
}
