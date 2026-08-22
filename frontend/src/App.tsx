import { Route, Routes } from "react-router";

import { AppShell } from "./components/AppShell";
import { AddressPage } from "./pages/AddressPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExplorerPage } from "./pages/ExplorerPage";
import { WatchlistPage } from "./pages/WatchlistPage";

function App() {
  return (
    <AppShell>
      <Routes>
        <Route
          path="/"
          element={<DashboardPage />}
        />

        <Route
          path="/addresses/:address"
          element={<AddressPage />}
        />

        <Route
          path="/explorer"
          element={<ExplorerPage />}
        />

        <Route
          path="/watchlist"
          element={<WatchlistPage />}
        />
      </Routes>
    </AppShell>
  );
}


export default App;
