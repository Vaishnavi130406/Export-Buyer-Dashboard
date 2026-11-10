import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Buyers from "./pages/Buyers";
import Search from "./pages/Search";
import BuyerSearch from "./pages/BuyerSearch";
import EmailCampaign from "./pages/EmailCampaign";
import History from "./pages/History";
import Settings from "./pages/Settings";
import LeadCRM from "./pages/LeadCRM";
import TeamReport from "./pages/TeamReport";

function App() {
    return (
        <BrowserRouter>
            <Routes>

                <Route
                    path="/"
                    element={<Navigate to="/dashboard" replace />}
                />

                <Route
                    path="/login"
                    element={<Login />}
                />

                <Route
                    path="/dashboard"
                    element={<Dashboard />}
                />

                <Route
                    path="/buyer-search"
                    element={<BuyerSearch />}
                />

                <Route
                    path="/buyers"
                    element={<Buyers />}
                />

                <Route
                    path="/search"
                    element={<Search />}
                />

                <Route
                    path="/campaign"
                    element={<EmailCampaign />}
                />

                <Route
                    path="/history"
                    element={<History />}
                />
                <Route path="/team-report" element={<TeamReport />} />
<Route path="/lead-crm" element={<LeadCRM />} />

                <Route
                    path="/settings"
                    element={<Settings />}
                />

                <Route
                    path="*"
                    element={
                        <div className="flex justify-center items-center h-screen text-3xl font-bold">
                            404 - Page Not Found
                        </div>
                    }
                />

            </Routes>
        </BrowserRouter>
    );
}

export default App;