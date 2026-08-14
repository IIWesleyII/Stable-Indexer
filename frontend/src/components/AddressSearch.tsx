import { FormEvent, useState } from "react";
import { useNavigate } from "react-router";


export function AddressSearch() {
  const [address, setAddress] = useState("");
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedAddress = address.trim();

    if (!normalizedAddress) {
      return;
    }

    navigate(
      `/addresses/${encodeURIComponent(normalizedAddress)}`,
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

      <button type="submit">
        Search
      </button>
    </form>
  );
}