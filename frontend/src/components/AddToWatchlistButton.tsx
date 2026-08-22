import { useEffect, useState } from "react";
import { BookmarkPlus } from "lucide-react";

import {
  addWatchlistAddress,
  getWatchlists,
} from "../api/watchlists";
import type { MetricsNetwork } from "../types/metrics";
import type { Watchlist } from "../types/watchlists";


interface AddToWatchlistButtonProps {
  address: string;
  chain?: MetricsNetwork;
}


export function AddToWatchlistButton({
  address,
  chain = "base",
}: AddToWatchlistButtonProps) {
  const [watchlists, setWatchlists] =
    useState<Watchlist[]>([]);

  const [watchlistId, setWatchlistId] =
    useState<number | null>(null);

  const [label, setLabel] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadWatchlists() {
      try {
        const result = await getWatchlists();

        setWatchlists(result);

        if (result.length > 0) {
          setWatchlistId(result[0].id);
        }
      } catch {
        setMessage("Failed to load watchlists");
      }
    }

    loadWatchlists();
  }, []);

  async function handleAdd() {
    if (watchlistId === null) {
      return;
    }

    try {
      setSaving(true);
      setMessage(null);

      await addWatchlistAddress(
        watchlistId,
        {
          address,
          label: label.trim() || undefined,
          chain,
        },
      );

      setMessage("Added to watchlist");
      setLabel("");
      setIsOpen(false);
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage(
          "Failed to add address",
        );
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="watchlist-add">
      <button
        className="watchlist-button"
        onClick={() => {
          setIsOpen((current) => !current);
          setMessage(null);
        }}
        type="button"
      >
        <BookmarkPlus aria-hidden="true" size={16} />
        Add to Watchlist
      </button>

      {isOpen && (
        <div className="watchlist-add-form">
          {watchlists.length === 0 ? (
            <p>No watchlists available.</p>
          ) : (
            <>
              <select
                onChange={(event) => {
                  setWatchlistId(
                    Number(event.target.value),
                  );
                }}
                value={watchlistId ?? ""}
              >
                {watchlists.map((watchlist) => (
                  <option
                    key={watchlist.id}
                    value={watchlist.id}
                  >
                    {watchlist.name}
                  </option>
                ))}
              </select>

              <input
                onChange={(event) => {
                  setLabel(event.target.value);
                }}
                placeholder="Optional label..."
                type="text"
                value={label}
              />

              <button
                disabled={saving}
                onClick={handleAdd}
                type="button"
              >
                {saving ? "Adding..." : "Add"}
              </button>
            </>
          )}
        </div>
      )}

      {message && (
        <span className="watchlist-message">
          {message}
        </span>
      )}
    </div>
  );
}
