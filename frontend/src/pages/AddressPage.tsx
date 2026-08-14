import { useState } from "react";
import { Link, useParams } from "react-router";

import { MetricCard } from "../components/MetricCard";
import { PartnersTable } from "../components/PartnersTable";
import { useAddress } from "../hooks/useAddress";
import { useAddressPartners } from "../hooks/useAddressPartners";
import type { PartnerSort } from "../types/addresses";


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

  const [partnerSort, setPartnerSort] =
    useState<PartnerSort>("volume");

  const {
    data,
    loading,
    error,
  } = useAddress(address);

  const partners = useAddressPartners(
    address,
    partnerSort,
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
          to="/"
        >
          ← Back to dashboard
        </Link>

        <p>
          {error ?? "Address unavailable"}
        </p>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <Link
        className="back-link"
        to="/"
      >
        ← Dashboard
      </Link>

      <header className="address-header">
        <div>
          <span className="page-label">
            Address
          </span>

          <h1 className="full-address">
            {data.address}
          </h1>

          <p>
            Indexed stablecoin activity for this
            address.
          </p>
        </div>
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
    </main>
  );
}