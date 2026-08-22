export interface MetricsSummary {
  transfer_count: number;
  total_volume: string;
  largest_transfer: string;
  smallest_transfer: string;
  unique_addresses: number;
}

export interface DailyVolume {
  date: string;
  token_symbol: string;
  transfer_count: number;
  volume: string;
}

export interface TopAddress {
  chain: string;
  address: string;
  transfer_count: number;
  sent_count: number;
  received_count: number;
  sent_volume: string;
  received_volume: string;
  activity_volume: string;
  usdc_activity_volume: string;
  usdt_activity_volume: string;
}

export type TopAddressSort = "transfer_count" | "volume";

export type MetricsNetwork =
  | "base"
  | "ethereum"
  | "solana"
  | "tron";

export type DashboardNetwork = MetricsNetwork | "all";
