import { useIndexerStatus } from "../hooks/useIndexerStatus";
import {
  ALL_NETWORKS,
  getDashboardNetworkLabel,
  getMetricsNetworkLabel,
  NETWORK_OPTIONS,
} from "../lib/networks";
import type {
  DashboardNetwork,
} from "../types/metrics";

interface NetworkStatusCardsProps {
  network: DashboardNetwork;
  onNetworkChange: (network: DashboardNetwork) => void;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function NetworkStatusCards({
  network,
  onNetworkChange,
}: NetworkStatusCardsProps) {
  const { data, error } = useIndexerStatus();

  return (
    <section
      aria-label="Network selection and indexer status"
      className="network-status-cards"
    >
      <button
        aria-pressed={network === ALL_NETWORKS}
        className={
          `network-status-card${
            network === ALL_NETWORKS ? " selected" : ""
          }`
        }
        onClick={() => onNetworkChange(ALL_NETWORKS)}
        type="button"
      >
        <span className="network-status-card-name">
          {getDashboardNetworkLabel(ALL_NETWORKS)}
        </span>
        <span className="network-status-card-state">
          {error
            ? "Status unavailable"
            : !data
              ? "Checking indexers"
              : `${data.length} indexers active`}
        </span>
      </button>

      {NETWORK_OPTIONS.map((option) => {
        const status = data?.find(
          (item) => item.chain === option.value,
        );
        const selected = option.value === network;
        const statusText = error
          ? "Status unavailable"
          : !data
            ? "Checking indexer"
            : !status
              ? "Not configured"
              : status.blocks_behind !== null
                && status.blocks_behind > 0
                ? `${formatNumber(status.blocks_behind)} blocks behind`
                : "Caught up";

        return (
          <button
            aria-pressed={selected}
            className={`network-status-card${selected ? " selected" : ""}`}
            key={option.value}
            onClick={() => onNetworkChange(option.value)}
            type="button"
          >
            <span className="network-status-card-name">
              {getMetricsNetworkLabel(option.value)}
            </span>
            <span className="network-status-card-state">
              {statusText}
            </span>
            {status && status.last_processed_block !== null && (
              <span className="network-status-card-block">
                {formatNumber(status.last_processed_block)}
                {" / "}
                {formatNumber(status.latest_block)}
              </span>
            )}
          </button>
        );
      })}
    </section>
  );
}
