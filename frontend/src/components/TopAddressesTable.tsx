import type {
  DashboardNetwork,
  MetricsNetwork,
  TopAddress,
  TopAddressSort,
} from "../types/metrics";
import { Bookmark } from "lucide-react";
import { Link } from "react-router";
import {
  ALL_NETWORKS,
  getMetricsNetworkLabel,
} from "../lib/networks";
import { AddressSearch } from "./AddressSearch";
interface TopAddressesTableProps {
  addresses: TopAddress[];
  network: DashboardNetwork;
  sortBy: TopAddressSort;
  onSortChange: (sortBy: TopAddressSort) => void;
}

function formatAddress(address: string): string {
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatVolume(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export function TopAddressesTable({
  addresses,
  network,
  sortBy,
  onSortChange,
}: TopAddressesTableProps) {
  const isAllNetworks = network === ALL_NETWORKS;

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <div>
          <h2>Top Addresses</h2>

          <p>
            Explore the most active stablecoin addresses.
          </p>
        </div>

        <div className="table-actions">
          <Link
            className="watchlist-table-link"
            to="/watchlist"
          >
            <Bookmark aria-hidden="true" size={15} />
            Watchlist
          </Link>

          {!isAllNetworks && (
            <AddressSearch network={network as MetricsNetwork} />
          )}

          <select
            value={sortBy}
            onChange={(event) => {
              onSortChange(
                event.target.value as TopAddressSort,
              );
            }}
          >
            <option value="volume">
              Highest Volume
            </option>

            <option value="transfer_count">
              Most Transfers
            </option>
          </select>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Address</th>
              {isAllNetworks && <th>Chain</th>}
              <th>Transfers</th>
              <th>USDC Volume</th>
              <th>USDT Volume</th>
              <th>Total Volume</th>
            </tr>
          </thead>

          <tbody>
            {addresses.map((address) => (
              <tr key={`${address.chain}:${address.address}`}>
                <td className="address-cell">
                  <Link
                    className="address-link"
                    to={
                      `/addresses/${address.address}?chain=`
                      + `${isAllNetworks ? address.chain : network}`
                    }
                  >
                    {formatAddress(address.address)}
                  </Link>
                </td>

                {isAllNetworks && (
                  <td>
                    {getMetricsNetworkLabel(
                      address.chain as MetricsNetwork,
                    )}
                  </td>
                )}

                <td>
                  {formatNumber(
                    address.transfer_count,
                  )}
                </td>

                <td>
                  {formatVolume(
                    address.usdc_activity_volume,
                  )}
                </td>

                <td>
                  {formatVolume(
                    address.usdt_activity_volume,
                  )}
                </td>

                <td>
                  {formatVolume(
                    address.activity_volume,
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
