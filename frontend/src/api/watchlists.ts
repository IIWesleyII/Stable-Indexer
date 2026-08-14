import type {
  AddWatchlistAddressRequest,
  Watchlist,
  WatchlistAddress,
  WatchlistDetail,
} from "../types/watchlists";


export async function getWatchlists(): Promise<Watchlist[]> {
  const response = await fetch("/api/watchlists");

  if (!response.ok) {
    throw new Error("Failed to load watchlists");
  }

  return response.json();
}


export async function getWatchlist(
  watchlistId: number,
): Promise<WatchlistDetail> {
  const response = await fetch(
    `/api/watchlists/${watchlistId}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load watchlist");
  }

  return response.json();
}


export async function addWatchlistAddress(
  watchlistId: number,
  request: AddWatchlistAddressRequest,
): Promise<WatchlistAddress> {
  const response = await fetch(
    `/api/watchlists/${watchlistId}/addresses`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );

  if (response.status === 409) {
    throw new Error(
      "This address is already in the watchlist",
    );
  }

  if (!response.ok) {
    throw new Error(
      "Failed to add address to watchlist",
    );
  }

  return response.json();
}


export async function removeWatchlistAddress(
  watchlistId: number,
  address: string,
  chain: string,
): Promise<void> {
  const params = new URLSearchParams({
    chain,
  });

  const encodedAddress =
    encodeURIComponent(address);

  const response = await fetch(
    `/api/watchlists/${watchlistId}/addresses/`
      + `${encodedAddress}?${params}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(
      "Failed to remove address from watchlist",
    );
  }
}