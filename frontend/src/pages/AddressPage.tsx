import { useState } from "react";
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

function formatUsdc(value: string): string {
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

export function AddressPage() {
  const { address } = useParams();
  const [searchParams, setSearchParams] =
    useSearchParams();

  const network = parseMetricsNetwork(
    searchParams.get("chain"),
  );

  const [partnerSort, setPartnerSort] =
    useState<PartnerSort>("volume");

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
      <main className="dashboard">
        <p>Loading address...</p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="dashboard">
        <Link
          className="back-link"
          to={`/?chain=${network}`}
        >
          {"<- Back to dashboard"}
        </Link>

        <p>
          {error ?? "Address unavailable"}
        </p>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <div className="address-page-nav">
        <Link
          className="back-link"
          to={`/?chain=${network}`}
        >
          {"<- Dashboard"}
        </Link>

        <div className="address-page-actions">
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

          <AddressSearch network={network} />
        </div>
      </div>

      <header className="address-header">
        <div>
          <span className="page-label">
            Address
          </span>

          <h1 className="full-address">
            {data.address}
          </h1>

          <p>
            {getMetricsNetworkLabel(network)}
            {" stablecoin activity for this address."}
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
          value={`${formatUsdc(
            data.sent_volume,
          )} USDC`}
        />

        <MetricCard
          label="Received"
          value={`${formatUsdc(
            data.received_volume,
          )} USDC`}
        />

        <MetricCard
          label="Net Flow"
          value={`${formatUsdc(
            data.net_flow,
          )} USDC`}
        />
      </section>

      <section className="address-details">
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

      {partners.loading && (
        <p>Loading partners...</p>
      )}

      {partners.error && (
        <p>{partners.error}</p>
      )}

      {!partners.loading
        && !partners.error && (
          <PartnersTable
            partners={partners.data}
            sortBy={partnerSort}
            onSortChange={setPartnerSort}
          />
        )}

      {activity.loading && (
        <p>Loading recent activity...</p>
      )}

      {activity.error && (
        <p>{activity.error}</p>
      )}

      {!activity.loading && !activity.error && (
        <RecentActivityTable activity={activity.data} />
      )}
    </main>
  );
}
