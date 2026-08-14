import { useIndexerStatus } from "../hooks/useIndexerStatus";


function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
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
        Loading indexer...
      </div>
    );
  }

  const statusLabel = data.caught_up
    ? "Caught up"
    : "Catching up";

  return (
    <div className="indexer-status">
      <div className="indexer-status-heading">
        <span className="status-dot" />

        <strong>
          Base Sepolia
        </strong>

        <span>
          {statusLabel}
        </span>
      </div>

      {data.last_processed_block !== null && (
        <div className="indexer-status-details">
          <span>
            {formatNumber(data.last_processed_block)}
            {" / "}
            {formatNumber(data.latest_block)}
          </span>

          {data.blocks_behind !== null
            && data.blocks_behind > 0 && (
              <span>
                {formatNumber(data.blocks_behind)}
                {" blocks behind"}
              </span>
            )}
        </div>
      )}
    </div>
  );
}