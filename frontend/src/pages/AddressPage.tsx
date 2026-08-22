import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import {
  Link,
  useParams,
  useSearchParams,
} from "react-router";

import { AddToWatchlistButton } from "../components/AddToWatchlistButton";
import { AddressSearch } from "../components/AddressSearch";
import { MetricCard } from "../components/MetricCard";
import { PartnersTable } from "../components/PartnersTable";
import { RecentActivityTable } from "../components/RecentActivityTable";
import { useAddress } from "../hooks/useAddress";
import { useAddressActivity } from "../hooks/useAddressActivity";
import { useAddressPartners } from "../hooks/useAddressPartners";
import {
  getMetricsNetworkLabel,
  NETWORK_OPTIONS,
  parseMetricsNetwork,
} from "../lib/networks";
import type { PartnerSort } from "../types/addresses";
import type { MetricsNetwork } from "../types/metrics";

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatStablecoinValue(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 6,
  }).format(Number(value));
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

type AddressView = "activity" | "partners";

export function AddressPage() {
  const { address } = useParams();
  const [searchParams, setSearchParams] =
    useSearchParams();

  const network = parseMetricsNetwork(
    searchParams.get("chain"),
  );

  const [partnerSort, setPartnerSort] =
    useState<PartnerSort>("volume");
  const [activeView, setActiveView] =
    useState<AddressView>("activity");

  function handleNetworkChange(nextNetwork: MetricsNetwork) {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("chain", nextNetwork);
    setSearchParams(nextParams);
  }

  const {
    data,
    loading,
    error,
  } = useAddress(
    address,
    network,
  );

  const partners = useAddressPartners(
    address,
    network,
    partnerSort,
  );

  const activity = useAddressActivity(
    address,
    network,
  );

  if (loading) {
    return (
      <main className="page">
        <p>Loading address...</p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="page">
        <Link
          className="back-link"
          to={`/?chain=${network}`}
        >
          <ArrowLeft aria-hidden="true" size={16} />
          Dashboard
        </Link>

        <p>
          {error ?? "Address unavailable"}
        </p>
      </main>
    );
  }

  return (
    <main className="page address-page">
      <div className="address-page-nav">
        <Link
          className="back-link"
          to={`/?chain=${network}`}
        >
          <ArrowLeft aria-hidden="true" size={16} />
          Dashboard
        </Link>

        <div className="address-page-actions">
          <label className="network-selector compact-control">
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

          <AddressSearch network={network} />
        </div>
      </div>

      <header className="address-header">
        <div>
          <span className="eyebrow">Address profile</span>

          <h1 className="full-address">
            {data.address}
          </h1>

          <p>
            <span className={`network-badge ${network}`}>
              {getMetricsNetworkLabel(network)}
            </span>
            {" indexed stablecoin activity"}
          </p>
        </div>

        <AddToWatchlistButton
          address={data.address}
          chain={network}
        />
      </header>

      <section className="metrics-grid">
        <MetricCard
          label="Transfers"
          value={formatNumber(
            data.transfer_count,
          )}
        />

        <MetricCard
          label="Sent"
          value={`${formatStablecoinValue(
            data.sent_volume,
          )} USDC / USDT`}
        />

        <MetricCard
          label="Received"
          value={`${formatStablecoinValue(
            data.received_volume,
          )} USDC / USDT`}
        />

        <MetricCard
          label="Net Flow"
          value={`${formatStablecoinValue(
            data.net_flow,
          )} USDC / USDT`}
        />
      </section>

      <section className="address-details" aria-label="Address details">
        <div>
          <span>Unique Partners</span>

          <strong>
            {formatNumber(
              data.unique_partners,
            )}
          </strong>
        </div>

        <div>
          <span>Sent Transfers</span>

          <strong>
            {formatNumber(
              data.sent_count,
            )}
          </strong>
        </div>

        <div>
          <span>Received Transfers</span>

          <strong>
            {formatNumber(
              data.received_count,
            )}
          </strong>
        </div>

        <div>
          <span>First Activity</span>

          <strong>
            {formatDate(
              data.first_activity,
            )}
          </strong>
        </div>

        <div>
          <span>Last Activity</span>

          <strong>
            {formatDate(
              data.last_activity,
            )}
          </strong>
        </div>
      </section>

      <div
        aria-label="Address data view"
        className="content-tabs"
        role="tablist"
      >
        <button
          aria-selected={activeView === "activity"}
          className={activeView === "activity" ? "active" : ""}
          onClick={() => setActiveView("activity")}
          role="tab"
          type="button"
        >
          Activity
        </button>
        <button
          aria-selected={activeView === "partners"}
          className={activeView === "partners" ? "active" : ""}
          onClick={() => setActiveView("partners")}
          role="tab"
          type="button"
        >
          Counterparties
        </button>
      </div>

      {activeView === "partners" && partners.loading && (
        <p>Loading counterparties...</p>
      )}

      {activeView === "partners" && partners.error && (
        <p>{partners.error}</p>
      )}

      {activeView === "partners" && !partners.loading && !partners.error && (
        <PartnersTable
          partners={partners.data}
          sortBy={partnerSort}
          onSortChange={setPartnerSort}
        />
      )}

      {activeView === "activity" && activity.loading && (
        <p>Loading recent activity...</p>
      )}

      {activeView === "activity" && activity.error && (
        <p>{activity.error}</p>
      )}

      {activeView === "activity" && !activity.loading && !activity.error && (
        <RecentActivityTable activity={activity.data} />
      )}
    </main>
  );
}
