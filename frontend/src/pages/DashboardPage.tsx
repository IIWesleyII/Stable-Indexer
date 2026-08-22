import { useState } from "react";
import { useSearchParams } from "react-router";
import { MetricCard } from "../components/MetricCard";
import { NetworkStatusCards } from "../components/NetworkStatusCards";
import { TopAddressesTable } from "../components/TopAddressesTable";
import { VolumeChart } from "../components/VolumeChart";
import { useDailyVolume } from "../hooks/useDailyVolume";
import { useSummaryMetrics } from "../hooks/useSummaryMetrics";
import { useTopAddresses } from "../hooks/useTopAddresses";
import type {
  DashboardNetwork,
  TopAddressSort,
} from "../types/metrics";
import {
  getDashboardNetworkLabel,
  parseDashboardNetwork,
} from "../lib/networks";

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatStablecoinValue(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function DashboardPage() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const [sortBy, setSortBy] =
    useState<TopAddressSort>("volume");

  const network = parseDashboardNetwork(
    searchParams.get("chain"),
  );

  function handleNetworkChange(nextNetwork: DashboardNetwork) {
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
    <main className="page dashboard">
      <header className="page-intro dashboard-header">
        <div>
          <h1>{getDashboardNetworkLabel(network)} Stablecoin Activity</h1>
        </div>

        <NetworkStatusCards
          network={network}
          onNetworkChange={handleNetworkChange}
        />
      </header>



      <section className="metrics-grid">
        <MetricCard
          label="Transfers"
          value={formatNumber(
            summary.data.transfer_count,
          )}
        />

        <MetricCard
          label="Total Volume (USDC + USDT)"
          value={`$${formatStablecoinValue(summary.data.total_volume)}`}
        />

        <MetricCard
          label="Largest Transfer (USDC / USDT)"
          value={`$${formatStablecoinValue(summary.data.largest_transfer)}`}
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
