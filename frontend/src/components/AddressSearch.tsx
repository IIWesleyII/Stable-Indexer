import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { Search } from "lucide-react";

import type { MetricsNetwork } from "../types/metrics";

interface AddressSearchProps {
  network?: MetricsNetwork;
}


export function AddressSearch({
  network,
}: AddressSearchProps) {
  const [address, setAddress] = useState("");
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedAddress = address.trim();

    if (!normalizedAddress) {
      return;
    }

    const path = `/addresses/${
      encodeURIComponent(normalizedAddress)
    }`;

    navigate(
      network
        ? `${path}?chain=${network}`
        : path,
    );

    setAddress("");
  }

  return (
    <form
      className="address-search"
      onSubmit={handleSubmit}
    >
      <input
        aria-label="Search address"
        onChange={(event) => setAddress(event.target.value)}
        placeholder="Search address..."
        type="text"
        value={address}
      />

      <button aria-label="Search address" title="Search address" type="submit">
        <Search aria-hidden="true" size={17} />
      </button>
    </form>
  );
}
