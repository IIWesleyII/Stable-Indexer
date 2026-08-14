import { Link } from "react-router";

import {
  removeWatchlistAddress,
} from "../api/watchlists";
import { useWatchlist } from "../hooks/useWatchlist";


function formatAddress(address: string): string {
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}


export function WatchlistPage() {
  const {
    watchlists,
    watchlist,
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

      await reload(watchlist.id);
    } catch (removeError) {
      console.error(removeError);
    }
  }

  if (loading) {
    return (
      <main className="dashboard">
        <p>Loading watchlist...</p>
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
            Addresses you want to keep an eye on.
          </p>
        </div>

        {watchlists.length > 1 && (
          <select
            onChange={(event) => {
              const id = Number(
                event.target.value,
              );

              setSelectedId(id);
              reload(id);
            }}
            value={selectedId ?? ""}
          >
            {watchlists.map((item) => (
              <option
                key={item.id}
                value={item.id}
              >
                {item.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {!watchlist && (
        <section className="dashboard-section">
          <p>No watchlists found.</p>
        </section>
      )}

      {watchlist && (
        <section className="dashboard-section">
          <div className="section-header">
            <div>
              <h2>{watchlist.name}</h2>

              <p>
                {watchlist.addresses.length}
                {" "}
                watched addresses
              </p>
            </div>
          </div>

          {watchlist.addresses.length === 0 ? (
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
                    <th>Chain</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {watchlist.addresses.map(
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
                          {item.chain}
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