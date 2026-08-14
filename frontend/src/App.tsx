import { Route, Routes } from "react-router";

import { AddressPage } from "./pages/AddressPage";
import { DashboardPage } from "./pages/DashboardPage";
import { WatchlistPage } from "./pages/WatchlistPage";

function App() {
  return (
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
        path="/watchlist"
        element={<WatchlistPage />}
      />
    </Routes>
  );
}


export default App;