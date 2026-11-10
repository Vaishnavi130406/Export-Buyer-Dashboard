import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../services/api";

import {
    FaSearch,
    FaBuilding,
    FaGlobe,
    FaEnvelope,
    FaDatabase,
    FaSpinner,
    FaCheckCircle,
    FaSave,
    FaMapMarkerAlt,
} from "react-icons/fa";

function BuyerSearch() {

    // ============================
    // FORM STATE
    // ============================

    const [product, setProduct] = useState("");
    const [country, setCountry] = useState("");
    const [state, setState] = useState("");
    const [city, setCity] = useState("");
    const [zipCode, setZipCode] = useState("");
    const [source, setSource] = useState("Google");

    // ============================
    // UI STATE
    // ============================

    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [selectedBuyers, setSelectedBuyers] = useState([]);

    // ============================
    // STATISTICS
    // ============================

    const [searchCount, setSearchCount] = useState(0);
    const [companiesFound, setCompaniesFound] = useState(0);
    const [emailsFound, setEmailsFound] = useState(0);
    const [websitesFound, setWebsitesFound] = useState(0);
    const [statesFound, setStatesFound] = useState(0);

    // ============================
    // UPDATE STATISTICS
    // ============================

    useEffect(() => {

        setCompaniesFound(results.length);

        setEmailsFound(
            results.filter(
                item => item.email && item.email.trim() !== ""
            ).length
        );

        setWebsitesFound(
            results.filter(
                item => item.website && item.website.trim() !== ""
            ).length
        );

        setStatesFound(
            new Set(
                results
                    .map(item => item.state)
                    .filter(Boolean)
            ).size
        );

    }, [results]);

    // ============================
    // SEARCH BUYERS
    // ============================

    const searchBuyers = async () => {

        if (!product.trim()) {
            alert("Please enter a product.");
            return;
        }

        if (!country.trim()) {
            alert("Please enter a country.");
            return;
        }

        try {

            setLoading(true);
            setResults([]);
            setSelectedBuyers([]);

            const res = await api.get("/api/search-buyers", {
                params: {
                    product,
                    country,
                    state,
                    city,
                    zip_code: zipCode,
                    source: source.toLowerCase(),
                    limit: 200,
                },
            });

            if (res.data.success) {

                const buyers = (res.data.results || []).map((buyer) => ({
                    company_name: buyer.company_name || "Unknown Company",
                    country: buyer.country || "",
                    state: buyer.state || "",
                    website: buyer.website || "",
                    email: buyer.email || "",
                    phone: buyer.phone || "",
                    city: buyer.city || "",
                    zip_code: buyer.zip_code || buyer.zipcode || "",
                    contact_person: buyer.contact_person || "",
                }));

                setResults(buyers);
                setSearchCount(prev => prev + 1);

            } else {

                alert(res.data.message || "Search failed.");

            }

        } catch (err) {

            console.error(err);

            alert(
                err.response?.data?.message ||
                "Unable to search buyers."
            );

        } finally {

            setLoading(false);

        }

    };
        // ============================
    // TOGGLE BUYER
    // ============================

    const toggleBuyer = (buyer) => {

        const exists = selectedBuyers.find(
            (b) => b.website === buyer.website
        );

        if (exists) {

            setSelectedBuyers(
                selectedBuyers.filter(
                    (b) => b.website !== buyer.website
                )
            );

        } else {

            setSelectedBuyers([
                ...selectedBuyers,
                buyer,
            ]);

        }

    };

    // ============================
    // SELECT / UNSELECT ALL
    // ============================

    const toggleSelectAll = () => {

        if (selectedBuyers.length === results.length) {

            setSelectedBuyers([]);

        } else {

            setSelectedBuyers([...results]);

        }

    };

    // ============================
    // SAVE SELECTED BUYERS
    // ============================

    const saveSelectedBuyers = async () => {

        if (selectedBuyers.length === 0) {

            alert("Please select at least one buyer.");
            return;

        }

        try {

            for (const buyer of selectedBuyers) {

                await api.post("/api/buyers", {

                    company_name: buyer.company_name || "Unknown Company",
                    country: buyer.country || "",
                    state: buyer.state || "",
                    website: buyer.website || "",
                    email: buyer.email || "",
                    phone: buyer.phone || "",
                    city: buyer.city || "",
                    zip_code: buyer.zip_code || "",
                    contact_person: buyer.contact_person || "",

                });

            }

            alert(`${selectedBuyers.length} buyer(s) saved successfully.`);

            setSelectedBuyers([]);

        } catch (err) {

            console.error(err);

            alert(
                err.response?.data?.message ||
                "Failed to save buyers."
            );

        }

    };

    // ============================
    // PAGE UI
    // ============================

    return (

        <Layout>

            <div className="space-y-8">

                {/* HERO SECTION */}

                <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-700 p-8 text-white shadow-2xl">

                    <div className="absolute -top-10 -right-10 w-56 h-56 rounded-full bg-white/10 blur-3xl"></div>

                    <div className="absolute -bottom-12 left-0 w-72 h-72 rounded-full bg-blue-400/10 blur-3xl"></div>

                    <div className="relative flex flex-col lg:flex-row justify-between gap-8">

                        <div>

                            <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full mb-5">

                                <FaGlobe />

                                <span className="text-sm">
                                    Global Buyer Search
                                </span>

                            </div>

                            <h1 className="text-4xl lg:text-5xl font-bold">
                                Buyer Discovery Portal
                            </h1>

                            <p className="text-blue-100 mt-4 max-w-2xl">
                                Search verified importers, wholesalers,
                                distributors and retailers worldwide.
                            </p>

                        </div>

                        <div className="bg-white/10 rounded-3xl p-7">

                            <div className="flex items-center gap-4">

                                <div className="bg-white/20 rounded-2xl p-4">

                                    <FaDatabase className="text-3xl" />

                                </div>

                                <div>

                                    <p className="text-sm">
                                        Searches
                                    </p>

                                    <h2 className="text-4xl font-bold">
                                        {searchCount}
                                    </h2>

                                </div>

                            </div>

                        </div>

                    </div>

                </div>
                                {/* ==========================================
                    STATISTICS
                =========================================== */}

                <div className="grid lg:grid-cols-5 md:grid-cols-2 gap-6">

                    <div className="bg-white rounded-3xl shadow-lg p-6">
                        <p className="text-gray-500 text-sm">Companies</p>
                        <h2 className="text-4xl font-bold mt-3">
                            {companiesFound}
                        </h2>
                    </div>

                    <div className="bg-white rounded-3xl shadow-lg p-6">
                        <p className="text-gray-500 text-sm">Websites</p>
                        <h2 className="text-4xl font-bold mt-3">
                            {websitesFound}
                        </h2>
                    </div>

                    <div className="bg-white rounded-3xl shadow-lg p-6">
                        <p className="text-gray-500 text-sm">Emails</p>
                        <h2 className="text-4xl font-bold mt-3">
                            {emailsFound}
                        </h2>
                    </div>

                    <div className="bg-white rounded-3xl shadow-lg p-6">
                        <p className="text-gray-500 text-sm">States</p>
                        <h2 className="text-4xl font-bold mt-3">
                            {statesFound}
                        </h2>
                    </div>

                    <div className="bg-white rounded-3xl shadow-lg p-6">
                        <p className="text-gray-500 text-sm">Selected</p>
                        <h2 className="text-4xl font-bold mt-3">
                            {selectedBuyers.length}
                        </h2>
                    </div>

                </div>

                {/* ==========================================
                    SEARCH FORM
                =========================================== */}

                <div className="bg-white rounded-3xl shadow-xl border border-slate-200 p-8">

                    <h2 className="text-3xl font-bold mb-6">
                        Search Buyers
                    </h2>

                    <div className="grid lg:grid-cols-7 md:grid-cols-2 gap-6">

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                Product
                            </label>

                            <input
                                value={product}
                                onChange={(e) => setProduct(e.target.value)}
                                placeholder="Rice"
                                className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                Country
                            </label>

                            <input
                                value={country}
                                onChange={(e) => setCountry(e.target.value)}
                                placeholder="USA"
                                className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                State
                            </label>

                            <input
                                value={state}
                                onChange={(e) => setState(e.target.value)}
                                placeholder="Florida"
                                className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                City
                            </label>

                            <input
                                value={city}
                                onChange={(e) => setCity(e.target.value)}
                                placeholder="Miami"
                                className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                ZIP Code
                            </label>

                            <input
                                value={zipCode}
                                onChange={(e) => setZipCode(e.target.value)}
                                placeholder="33101"
                                className="w-full rounded-xl border border-slate-300 px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold mb-2">
                                Source
                            </label>

                            <select
                                value={source}
                                onChange={(e) => setSource(e.target.value)}
                                className="w-full rounded-xl border border-slate-300 px-4 py-3"
                            >
                                <option value="Google">Google</option>
                                <option value="Alibaba">Alibaba</option>
                                <option value="IndiaMART">IndiaMART</option>
                                <option value="TradeIndia">TradeIndia</option>
                                <option value="ExportersIndia">ExportersIndia</option>
                            </select>
                        </div>

                        <div className="flex items-end">

                            <button
                                onClick={searchBuyers}
                                disabled={loading}
                                className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 font-semibold shadow-lg hover:scale-105 transition disabled:opacity-60"
                            >

                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <FaSpinner className="animate-spin" />
                                        Searching...
                                    </span>
                                ) : (
                                    <span className="flex items-center justify-center gap-2">
                                        <FaSearch />
                                        Search Buyers
                                    </span>
                                )}

                            </button>

                        </div>

                    </div>

                </div>
                                {/* ==========================================
                    SEARCH RESULTS
                =========================================== */}

                <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">

                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5 px-8 py-6 border-b">

                        <div>

                            <h2 className="text-2xl font-bold">
                                Search Results
                            </h2>

                            <p className="text-gray-500 mt-2">
                                {results.length} buyers found
                            </p>

                        </div>

                        {results.length > 0 && (

                            <button
                                onClick={toggleSelectAll}
                                className="px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold"
                            >

                                {selectedBuyers.length === results.length
                                    ? "Unselect All"
                                    : "Select All"}

                            </button>

                        )}

                    </div>

                    {loading ? (

                        <div className="py-20 flex flex-col items-center">

                            <FaSpinner className="animate-spin text-5xl text-blue-600" />

                            <p className="mt-5 text-lg">
                                Searching buyers...
                            </p>

                        </div>

                    ) : results.length === 0 ? (

                        <div className="py-20 text-center">

                            <FaSearch className="mx-auto text-6xl text-gray-300" />

                            <p className="mt-5 text-gray-500">
                                No buyers found.
                            </p>

                        </div>

                    ) : (

                        <div className="overflow-x-auto">

                            <table className="min-w-full">

                                <thead className="bg-slate-100">

                                    <tr>

                                        <th className="px-4 py-4">Select</th>
                                        <th className="px-4 py-4 text-left">Company</th>
                                        <th className="px-4 py-4 text-left">Country</th>
                                        <th className="px-4 py-4 text-left">State</th>
                                        <th className="px-4 py-4 text-left">City</th>
                                        <th className="px-4 py-4 text-left">ZIP Code</th>
                                        <th className="px-4 py-4 text-left">Website</th>
                                        <th className="px-4 py-4 text-left">Email</th>

                                    </tr>

                                </thead>

                                <tbody>

                                    {results.map((buyer, index) => {

                                        const checked = selectedBuyers.find(
                                            (b) => b.website === buyer.website
                                        );

                                        return (

                                            <tr
                                                key={index}
                                                className="border-b hover:bg-slate-50"
                                            >

                                                <td className="px-4 py-4 text-center">

                                                    <input
                                                        type="checkbox"
                                                        checked={!!checked}
                                                        onChange={() => toggleBuyer(buyer)}
                                                    />

                                                </td>

                                                <td className="px-4 py-4">

                                                    <div className="flex items-center gap-2">

                                                        <FaBuilding className="text-blue-600" />

                                                        <span className="font-medium">
                                                            {buyer.company_name}
                                                        </span>

                                                    </div>

                                                </td>

                                                <td className="px-4 py-4">
                                                    {buyer.country || "-"}
                                                </td>

                                                <td className="px-4 py-4">
                                                    {buyer.state || "-"}
                                                </td>

                                                <td className="px-4 py-4">
                                                    {buyer.city || "-"}
                                                </td>

                                                <td className="px-4 py-4">
                                                    {buyer.zip_code || "-"}
                                                </td>

                                                <td className="px-4 py-4">

                                                    {buyer.website ? (

                                                        <a
                                                            href={buyer.website}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="text-blue-600 hover:underline"
                                                        >
                                                            Visit Website
                                                        </a>

                                                    ) : (

                                                        "-"

                                                    )}

                                                </td>

                                                <td className="px-4 py-4">

                                                    {buyer.email ? (

                                                        <div className="flex items-center gap-2">

                                                            <FaEnvelope className="text-green-600" />

                                                            {buyer.email}

                                                        </div>

                                                    ) : (

                                                        "Email Not Found"

                                                    )}

                                                </td>

                                            </tr>

                                        );

                                    })}

                                </tbody>

                            </table>

                        </div>

                    )}

                </div>
                                {/* ==========================================
                    ACTION BAR
                =========================================== */}

                {results.length > 0 && (

                    <div className="bg-white rounded-3xl shadow-xl border border-slate-200 p-8">

                        <div className="flex flex-col lg:flex-row justify-between items-center gap-6">

                            <div>

                                <h2 className="text-2xl font-bold">
                                    Buyer Summary
                                </h2>

                                <p className="text-gray-500 mt-2">
                                    {selectedBuyers.length} buyer(s) selected
                                </p>

                            </div>

                            <div className="flex gap-4">

                                <button
                                    onClick={() => setSelectedBuyers([])}
                                    className="px-6 py-3 rounded-xl border border-gray-300 hover:bg-gray-100"
                                >
                                    Clear Selection
                                </button>

                                <button
                                    onClick={saveSelectedBuyers}
                                    disabled={selectedBuyers.length === 0}
                                    className="px-8 py-3 rounded-xl bg-green-600 text-white font-semibold flex items-center gap-2 disabled:opacity-50"
                                >
                                    <FaSave />
                                    Save Selected Buyers
                                </button>

                            </div>

                        </div>

                    </div>

                )}

            </div>

        </Layout>

    );

}

export default BuyerSearch;