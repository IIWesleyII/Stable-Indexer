import { useState } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DailyVolume } from "../types/metrics";

interface VolumeChartProps {
  data: DailyVolume[];
  networkLabel: string;
}

type ChartMode = "volume" | "count";

function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatFullDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function VolumeChart({
  data,
  networkLabel,
}: VolumeChartProps) {
  const [mode, setMode] = useState<ChartMode>("volume");

  const chartData = data.map((item) => ({
    ...item,
    volume: Number(item.volume),
  }));

  const firstDate = data.at(0)?.date;
  const lastDate = data.at(-1)?.date;

  const dataKey = mode === "volume"
    ? "volume"
    : "transfer_count";

  const label = mode === "volume"
    ? "Transfer Volume"
    : "Transfer Count";

  return (
    <section className="dashboard-section">
      <div className="section-header chart-header">
        <div>
          <h2>Daily Stablecoin Activity</h2>

          <p>
            {networkLabel}
            {" - USDC - Transfers only"}
          </p>

          {firstDate && lastDate && (
            <span className="chart-date-range">
              {formatFullDate(firstDate)}
              {" - "}
              {formatFullDate(lastDate)}
            </span>
          )}
        </div>

        <div className="chart-toggle">
          <button
            className={mode === "volume" ? "active" : ""}
            onClick={() => setMode("volume")}
            type="button"
          >
            Transfer Volume
          </button>

          <button
            className={mode === "count" ? "active" : ""}
            onClick={() => setMode("count")}
            type="button"
          >
            Transfer Count
          </button>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
            />

            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
            />

            <YAxis
              tickFormatter={formatCompact}
              width={70}
            />

            <Tooltip
              labelFormatter={(value) => {
                return formatFullDate(String(value));
              }}
              formatter={(value) => {
                const numberValue = Number(value);

                if (mode === "volume") {
                  return [
                    `${numberValue.toLocaleString()} USDC`,
                    label,
                  ];
                }

                return [
                  numberValue.toLocaleString(),
                  label,
                ];
              }}
            />

            <Bar
              dataKey={dataKey}
              name={label}
              fill="currentColor"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
