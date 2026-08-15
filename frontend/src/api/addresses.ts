import type {AddressPartner, AddressSummary, PartnerSort, AddressActivity} from "../types/addresses";

export async function getAddressSummary(
  address: string,
): Promise<AddressSummary> {
  const response = await fetch(
    `/api/addresses/${address}`,
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
  limit = 10,
  sortBy: PartnerSort = "volume",
): Promise<AddressPartner[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    sort_by: sortBy,
  });

  const response = await fetch(
    `/api/addresses/${address}/partners?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load address partners");
  }

  return response.json();
}

export async function getAddressActivity(
  address: string,
  limit = 20,
): Promise<AddressActivity[]> {
  const params = new URLSearchParams({
    limit: String(limit),
  });

  const response = await fetch(
    `/api/addresses/${encodeURIComponent(address)}/activity?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load address activity");
  }

  return response.json();
}