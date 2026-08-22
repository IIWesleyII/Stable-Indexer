import { Search } from "lucide-react";
import { useSearchParams } from "react-router";

import { AddressSearch } from "../components/AddressSearch";
import {
  getMetricsNetworkLabel,
  NETWORK_OPTIONS,
  parseMetricsNetwork,
} from "../lib/networks";
import type { MetricsNetwork } from "../types/metrics";

export function ExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const network = parseMetricsNetwork(searchParams.get("chain"));

  function handleNetworkChange(nextNetwork: MetricsNetwork) {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("chain", nextNetwork);
    setSearchParams(nextParams);
  }

  return (
    <main className="page explorer-page">
      <header className="page-intro page-intro-with-control">
        <div>
          <span className="eyebrow">Address intelligence</span>
          <h1>Explorer</h1>
          <p>Inspect indexed stablecoin activity on a selected network.</p>
        </div>

        <label className="network-selector compact-control">
          <span>Network</span>
          <select
            onChange={(event) => {
              handleNetworkChange(event.target.value as MetricsNetwork);
            }}
            value={network}
          >
            {NETWORK_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </header>

      <section className="explorer-search-surface">
        <div className="explorer-search-icon">
          <Search aria-hidden="true" size={22} />
        </div>
        <div>
          <span className="eyebrow">{getMetricsNetworkLabel(network)}</span>
          <h2>Look up an address</h2>
        </div>
        <AddressSearch network={network} />
      </section>
    </main>
  );
}
