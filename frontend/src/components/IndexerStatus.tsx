import { useIndexerStatus } from "../hooks/useIndexerStatus";
import { getMetricsNetworkLabel } from "../lib/networks";
import type { MetricsNetwork } from "../types/metrics";

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatChain(chain: string): string {
  if (chain === "base" || chain === "base-sepolia") {
    return getMetricsNetworkLabel(chain as MetricsNetwork);
  }

  return chain;
}

export function IndexerStatus() {
  const {
    data,
    error,
  } = useIndexerStatus();

  if (error) {
    return (
      <div className="indexer-status error">
        Indexer unavailable
      </div>
    );
  }

  if (!data) {
    return (
      <div className="indexer-status">
        Loading indexers...
      </div>
    );
  }

  return (
    <div className="indexer-status-list">
      {data.map((status) => {
        const statusLabel = status.caught_up
          ? "Caught up"
          : "Catching up";

        return (
          <div
            className="indexer-status"
            key={status.chain}
          >
            <div className="indexer-status-heading">
              <span className="status-dot" />

              <strong>
                {formatChain(status.chain)}
              </strong>

              <span>
                {statusLabel}
              </span>
            </div>

            {status.last_processed_block !== null && (
              <div className="indexer-status-details">
                <span>
                  {formatNumber(status.last_processed_block)}
                  {" / "}
                  {formatNumber(status.latest_block)}
                </span>

                {status.blocks_behind !== null
                  && status.blocks_behind > 0 && (
                    <span>
                      {formatNumber(status.blocks_behind)}
                      {" blocks behind"}
                    </span>
                  )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
