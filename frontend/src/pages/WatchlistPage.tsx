import { Link } from "react-router";

import {
  removeWatchlistAddress,
} from "../api/watchlists";
import { useWatchlist } from "../hooks/useWatchlist";


function formatAddress(address: string): string {
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}


function formatNumber(value: number): string {
  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}


function formatVolume(value: string): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits: 6,
    },
  ).format(Number(value));
}


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Date(
    value,
  ).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}


function getNetFlowClass(
  value: string,
): string {
  const numericValue = Number(value);

  if (numericValue > 0) {
    return "net-flow-positive";
  }

  if (numericValue < 0) {
    return "net-flow-negative";
  }

  return "";
}


export function WatchlistPage() {
  const {
    watchlists,
    watchlist,
    analytics,
    selectedId,
    loading,
    error,
    setSelectedId,
    reload,
  } = useWatchlist();

  async function handleRemove(
    address: string,
    chain: string,
  ) {
    if (!watchlist) {
      return;
    }

    try {
      await removeWatchlistAddress(
        watchlist.id,
        address,
        chain,
      );

      await reload(
        watchlist.id,
      );
    } catch (removeError) {
      console.error(removeError);
    }
  }

  async function handleWatchlistChange(
    watchlistId: number,
  ) {
    setSelectedId(watchlistId);

    await reload(
      watchlistId,
    );
  }

  if (loading) {
    return (
      <main className="dashboard">
        <p>
          Loading watchlist...
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="dashboard">
        <Link
          className="back-link"
          to="/"
        >
          ← Dashboard
        </Link>

        <p>{error}</p>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <div className="watchlist-page-header">
        <div>
          <Link
            className="back-link"
            to="/"
          >
            ← Dashboard
          </Link>

          <h1>Watchlist</h1>

          <p>
            Monitor stablecoin activity for
            addresses you care about.
          </p>
        </div>

        {watchlists.length > 1 && (
          <select
            onChange={(event) => {
              handleWatchlistChange(
                Number(
                  event.target.value,
                ),
              );
            }}
            value={selectedId ?? ""}
          >
            {watchlists.map(
              (item) => (
                <option
                  key={item.id}
                  value={item.id}
                >
                  {item.name}
                </option>
              ),
            )}
          </select>
        )}
      </div>

      {!watchlist && (
        <section className="dashboard-section">
          <p>
            No watchlists found.
          </p>
        </section>
      )}

      {watchlist && (
        <section className="dashboard-section">
          <div className="section-header">
            <div>
              <h2>
                {watchlist.name}
              </h2>

              <p>
                {analytics.length}
                {" "}
                watched
                {" "}
                {analytics.length === 1
                  ? "address"
                  : "addresses"}
              </p>
            </div>
          </div>

          {analytics.length === 0 ? (
            <p>
              No addresses have been added yet.
            </p>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Address</th>
                    <th>Label</th>
                    <th>Transfers</th>
                    <th>Sent</th>
                    <th>Received</th>
                    <th>Net Flow</th>
                    <th>Partners</th>
                    <th>Last Activity</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {analytics.map(
                    (item) => (
                      <tr key={item.id}>
                        <td className="address-cell">
                          <Link
                            className="address-link"
                            to={
                              `/addresses/${item.address}`
                            }
                          >
                            {formatAddress(
                              item.address,
                            )}
                          </Link>
                        </td>

                        <td>
                          {item.label ?? "—"}
                        </td>

                        <td>
                          {formatNumber(
                            item.transfer_count,
                          )}
                        </td>

                        <td>
                          {formatVolume(
                            item.sent_volume,
                          )}
                          {" "}
                          USDC
                        </td>

                        <td>
                          {formatVolume(
                            item.received_volume,
                          )}
                          {" "}
                          USDC
                        </td>

                        <td
                          className={
                            getNetFlowClass(
                              item.net_flow,
                            )
                          }
                        >
                          {formatVolume(
                            item.net_flow,
                          )}
                          {" "}
                          USDC
                        </td>

                        <td>
                          {formatNumber(
                            item.unique_partners,
                          )}
                        </td>

                        <td>
                          {formatDate(
                            item.last_activity,
                          )}
                        </td>

                        <td>
                          <button
                            className="remove-button"
                            onClick={() => {
                              handleRemove(
                                item.address,
                                item.chain,
                              );
                            }}
                            type="button"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
}