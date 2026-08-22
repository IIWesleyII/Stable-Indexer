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
import { buildDailyActivityChartData } from "../lib/dailyActivity";

interface VolumeChartProps {
  data: DailyVolume[];
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
}: VolumeChartProps) {
  const [mode, setMode] = useState<ChartMode>("volume");

  const chartData = buildDailyActivityChartData(data);

  const usdcDataKey = mode === "volume"
    ? "usdc_volume"
    : "usdc_transfer_count";

  const usdtDataKey = mode === "volume"
    ? "usdt_volume"
    : "usdt_transfer_count";

  return (
    <section className="dashboard-section">
      <div className="section-header chart-header">
        <div>
          <h2>Daily Stablecoin Activity</h2>

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

      <div className="chart-legend">
        <span className="token-legend usdc">
          <i />
          USDC
        </span>
        <span className="token-legend usdt">
          <i />
          USDT
        </span>
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
              formatter={(value, name) => {
                const numberValue = Number(value);

                return [
                  numberValue.toLocaleString(),
                  name,
                ];
              }}
            />

            <Bar
              dataKey={usdcDataKey}
              name="USDC"
              fill="#2775ca"
              radius={[4, 4, 0, 0]}
            />

            <Bar
              dataKey={usdtDataKey}
              name="USDT"
              fill="#26a17b"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
