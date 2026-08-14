import { useEffect, useState } from "react";

import { getAddressPartners } from "../api/addresses";
import type {
  AddressPartner,
  PartnerSort,
} from "../types/addresses";


export function useAddressPartners(
  address: string | undefined,
  sortBy: PartnerSort,
  limit = 10,
) {
  const [data, setData] = useState<AddressPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!address) {
      setLoading(false);
      return;
    }

    async function loadPartners() {
      try {
        setLoading(true);
        setError(null);

        const partners = await getAddressPartners(
          address!,
          limit,
          sortBy,
        );

        setData(partners);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load partners");
        }
      } finally {
        setLoading(false);
      }
    }

    loadPartners();
  }, [
    address,
    limit,
    sortBy,
  ]);

  return {
    data,
    loading,
    error,
  };
}