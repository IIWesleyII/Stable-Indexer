import { Link } from "react-router";

import type { AddressActivity } from "../types/addresses";


interface RecentActivityTableProps {
  activity: AddressActivity[];
}


function formatAddress(address: string): string {
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}


function formatAmount(value: string): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 6,
  }).format(Number(value));
}


function formatDate(value: string): string {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}


function formatDirection(direction: AddressActivity["direction"]): string {
  if (direction === "sent") {
    return "Sent";
  }

  if (direction === "received") {
    return "Received";
  }

  return "Self";
}


export function RecentActivityTable({
  activity,
}: RecentActivityTableProps) {
  return (
    <section className="dashboard-section">
      <div className="section-header">
        <div>
          <h2>Recent Activity</h2>

          <p>Most recent indexed stablecoin transfers.</p>
        </div>
      </div>

      {activity.length === 0 ? (
        <p>No recent transfer activity.</p>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Direction</th>
                <th>Counterparty</th>
                <th>Amount</th>
                <th>Block</th>
              </tr>
            </thead>

            <tbody>
              {activity.map((transfer) => (
                <tr
                  key={
                    `${transfer.transaction_hash}-${transfer.log_index}`
                  }
                >
                  <td>{formatDate(transfer.timestamp)}</td>

                  <td>
                    <span
                      className={`activity-direction ${transfer.direction}`}
                    >
                      {formatDirection(transfer.direction)}
                    </span>
                  </td>

                  <td className="address-cell">
                    <Link
                      className="address-link"
                      to={`/addresses/${transfer.counterparty}`}
                    >
                      {formatAddress(transfer.counterparty)}
                    </Link>
                  </td>

                  <td>
                    {formatAmount(transfer.amount)}
                    {" "}
                    {transfer.token_symbol}
                  </td>

                  <td>
                    {new Intl.NumberFormat("en-US").format(
                      transfer.block_number,
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}