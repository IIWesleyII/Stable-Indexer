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