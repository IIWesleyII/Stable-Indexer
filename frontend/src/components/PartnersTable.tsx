import { Link } from "react-router";

import type {
  AddressPartner,
  PartnerSort,
} from "../types/addresses";


interface PartnersTableProps {
  partners: AddressPartner[];
  sortBy: PartnerSort;
  onSortChange: (sortBy: PartnerSort) => void;
}


function formatAddress(address: string): string {
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}


function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}


function formatVolume(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 6,
  }).format(Number(value));
}


export function PartnersTable({
  partners,
  sortBy,
  onSortChange,
}: PartnersTableProps) {
  return (
    <section className="dashboard-section">
      <div className="section-header">
        <div>
          <h2>Top Partners</h2>

          <p>
            Addresses this wallet interacts with most.
          </p>
        </div>

        <select
          value={sortBy}
          onChange={(event) => {
            onSortChange(
              event.target.value as PartnerSort,
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

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Partner</th>
              <th>Transfers</th>
              <th>Sent</th>
              <th>Received</th>
              <th>Volume</th>
            </tr>
          </thead>

          <tbody>
            {partners.map((partner) => (
              <tr key={partner.address}>
                <td className="address-cell">
                  <Link
                    className="address-link"
                    to={`/addresses/${partner.address}`}
                  >
                    {formatAddress(partner.address)}
                  </Link>
                </td>

                <td>
                  {formatNumber(
                    partner.transfer_count,
                  )}
                </td>

                <td>
                  {formatVolume(
                    partner.sent_volume,
                  )}
                </td>

                <td>
                  {formatVolume(
                    partner.received_volume,
                  )}
                </td>

                <td>
                  {formatVolume(
                    partner.activity_volume,
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