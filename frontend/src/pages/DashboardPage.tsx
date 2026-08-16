import { useState } from "react";
import { useSearchParams } from "react-router";
import { IndexerStatus } from "../components/IndexerStatus";
import { MetricCard } from "../components/MetricCard";
import { TopAddressesTable } from "../components/TopAddressesTable";
import { VolumeChart } from "../components/VolumeChart";
import { useDailyVolume } from "../hooks/useDailyVolume";
import { useSummaryMetrics } from "../hooks/useSummaryMetrics";
import { useTopAddresses } from "../hooks/useTopAddresses";
import type {
  MetricsNetwork,
  TopAddressSort,
} from "../types/metrics";
import {
  getMetricsNetworkLabel,
  NETWORK_OPTIONS,
  parseMetricsNetwork,
} from "../lib/networks";

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatUsdc(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function DashboardPage() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const [sortBy, setSortBy] =
    useState<TopAddressSort>("volume");

  const network = parseMetricsNetwork(
    searchParams.get("chain"),
  );

  function handleNetworkChange(nextNetwork: MetricsNetwork) {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("chain", nextNetwork);
    setSearchParams(nextParams);
  }

  const summary = useSummaryMetrics(network);
  const dailyVolume = useDailyVolume(network, 30);
  const topAddresses = useTopAddresses(
    network,
    sortBy,
  );

  if (summary.loading) {
    return (
      <main className="dashboard">
        <p>Loading Stable Indexer...</p>
      </main>
    );
  }

  if (summary.error || !summary.data) {
    return (
      <main className="dashboard">
        <p>
          {summary.error
            ?? "Unable to load dashboard."}
        </p>
      </main>
    );
  }

  return (
    <main className="dashboard">
    <header className="dashboard-header">
      <div>
        <h1>Stable Indexer</h1>

        <p>
          Stablecoin intelligence across blockchain
          networks.
        </p>
      </div>

      <div className="dashboard-header-actions">
        <label className="network-selector">
          <span>Network</span>

          <select
            value={network}
            onChange={(event) => {
              handleNetworkChange(
                event.target.value as MetricsNetwork,
              );
            }}
          >
            {NETWORK_OPTIONS.map((option) => (
              <option
                key={option.value}
                value={option.value}
              >
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <IndexerStatus />
      </div>
    </header>

      <section className="metrics-grid">
        <MetricCard
          label="Transfers"
          value={formatNumber(
            summary.data.transfer_count,
          )}
        />

        <MetricCard
          label="Total Volume"
          value={
            `${formatUsdc(
              summary.data.total_volume,
            )} USDC`
          }
        />

        <MetricCard
          label="Largest Transfer"
          value={
            `${formatUsdc(
              summary.data.largest_transfer,
            )} USDC`
          }
        />

        <MetricCard
          label="Unique Addresses"
          value={formatNumber(
            summary.data.unique_addresses,
          )}
        />
      </section>

      {dailyVolume.loading && (
        <p>Loading volume data...</p>
      )}

      {dailyVolume.error && (
        <p>{dailyVolume.error}</p>
      )}

      {!dailyVolume.loading
        && !dailyVolume.error && (
          <VolumeChart
            data={dailyVolume.data}
            networkLabel={getMetricsNetworkLabel(
              network,
            )}
          />
        )}

      {topAddresses.loading && (
        <p>Loading top addresses...</p>
      )}

      {topAddresses.error && (
        <p>{topAddresses.error}</p>
      )}

      {!topAddresses.loading
        && !topAddresses.error && (
          <TopAddressesTable
            addresses={topAddresses.data}
            network={network}
            sortBy={sortBy}
            onSortChange={setSortBy}
          />
        )}
    </main>
  );
}
