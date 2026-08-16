import type {
  AddressActivity,
  AddressPartner,
  AddressSummary,
  PartnerSort,
} from "../types/addresses";
import type { MetricsNetwork } from "../types/metrics";

export async function getAddressSummary(
  address: string,
  chain: MetricsNetwork,
): Promise<AddressSummary> {
  const params = new URLSearchParams({
    chain,
    stablecoin: "USDC",
  });

  const response = await fetch(
    `/api/addresses/${
      encodeURIComponent(address)
    }?${params}`,
  );

  if (response.status === 404) {
    throw new Error(
      "No indexed activity found for this address",
    );
  }

  if (!response.ok) {
    throw new Error(
      "Failed to load address",
    );
  }

  return response.json();
}

export async function getAddressPartners(
  address: string,
  chain: MetricsNetwork,
  limit = 10,
  sortBy: PartnerSort = "volume",
): Promise<AddressPartner[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    sort_by: sortBy,
    chain,
    stablecoin: "USDC",
  });

  const response = await fetch(
    `/api/addresses/${
      encodeURIComponent(address)
    }/partners?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load address partners");
  }

  return response.json();
}

export async function getAddressActivity(
  address: string,
  chain: MetricsNetwork,
  limit = 20,
): Promise<AddressActivity[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    chain,
    stablecoin: "USDC",
  });

  const response = await fetch(
    `/api/addresses/${encodeURIComponent(address)}/activity?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load address activity");
  }

  return response.json();
}
