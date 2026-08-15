export interface Watchlist {
  id: number;
  name: string;
  created_at: string;
}

export interface WatchlistAddress {
  id: number;
  address: string;
  label: string | null;
  chain: string;
  created_at: string;
}

export interface WatchlistDetail extends Watchlist {
  addresses: WatchlistAddress[];
}

export interface AddWatchlistAddressRequest {
  address: string;
  label?: string;
  chain: string;
}

export interface WatchlistAddressAnalytics {
  id: number;
  address: string;
  label: string | null;
  chain: string;
  transfer_count: number;
  sent_count: number;
  received_count: number;
  sent_volume: string;
  received_volume: string;
  net_flow: string;
  unique_partners: number;
  last_activity: string | null;
}