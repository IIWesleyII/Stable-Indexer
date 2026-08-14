import { Route, Routes } from "react-router";

import { AddressPage } from "./pages/AddressPage";
import { DashboardPage } from "./pages/DashboardPage";


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
    </Routes>
  );
}


export default App;