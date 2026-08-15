import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getWatchlist,
  getWatchlistAnalytics,
  getWatchlists,
} from "../api/watchlists";
import type {
  Watchlist,
  WatchlistAddressAnalytics,
  WatchlistDetail,
} from "../types/watchlists";


export function useWatchlist() {
  const [watchlists, setWatchlists] =
    useState<Watchlist[]>([]);

  const [selectedId, setSelectedId] =
    useState<number | null>(null);

  const [watchlist, setWatchlist] =
    useState<WatchlistDetail | null>(null);

  const [analytics, setAnalytics] =
    useState<WatchlistAddressAnalytics[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadWatchlist = useCallback(
    async (watchlistId?: number) => {
      try {
        setLoading(true);
        setError(null);

        const lists = await getWatchlists();

        setWatchlists(lists);

        if (lists.length === 0) {
          setWatchlist(null);
          setAnalytics([]);
          return;
        }

        const id =
          watchlistId
          ?? selectedId
          ?? lists[0].id;

        setSelectedId(id);

        const [
          detail,
          analyticsResult,
        ] = await Promise.all([
          getWatchlist(id),
          getWatchlistAnalytics(id),
        ]);

        setWatchlist(detail);
        setAnalytics(analyticsResult);
      } catch (loadError) {
        if (loadError instanceof Error) {
          setError(loadError.message);
        } else {
          setError(
            "Failed to load watchlist",
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [selectedId],
  );

  useEffect(() => {
    loadWatchlist();
  }, [loadWatchlist]);

  return {
    watchlists,
    watchlist,
    analytics,
    selectedId,
    loading,
    error,
    setSelectedId,
    reload: loadWatchlist,
  };
}