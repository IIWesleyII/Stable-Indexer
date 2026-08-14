import type {TopAddress,TopAddressSort} from "../types/metrics";
import { Link } from "react-router";
import { AddressSearch } from "./AddressSearch";
interface TopAddressesTableProps {
  addresses: TopAddress[];
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
  sortBy,
  onSortChange,
}: TopAddressesTableProps) {
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
            Watchlist
          </Link>

          <AddressSearch />

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
              <th>Transfers</th>
              <th>Sent</th>
              <th>Received</th>
              <th>Volume</th>
            </tr>
          </thead>

          <tbody>
            {addresses.map((address) => (
              <tr key={address.address}>
                <td className="address-cell">
                  <Link
                    className="address-link"
                    to={`/addresses/${address.address}`}
                  >
                    {formatAddress(address.address)}
                  </Link>
                </td>

                <td>
                  {formatNumber(
                    address.transfer_count,
                  )}
                </td>

                <td>
                  {formatVolume(
                    address.sent_volume,
                  )}
                </td>

                <td>
                  {formatVolume(
                    address.received_volume,
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