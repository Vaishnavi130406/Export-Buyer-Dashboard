import { useEffect, useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";

import {
    FaSearch,
    FaBuilding,
    FaGlobe,
    FaEnvelope,
    FaDatabase,
    FaSpinner,
    FaSave,
} from "react-icons/fa";

// Flask backend runs on port 5000 in your project.
// You can override this with VITE_API_URL in .env if needed.
const API_BASE_URL = (
    import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"
).replace(/\/$/, "");

const buyerApi = axios.create({
    baseURL: API_BASE_URL,
    timeout: 180000,
    headers: {
        Accept: "application/json",
    },
});

function BuyerSearch() {
    const [product, setProduct] = useState("");
    const [country, setCountry] = useState("");
    const [state, setState] = useState("");
    const [city, setCity] = useState("");
    const [zipCode, setZipCode] = useState("");
    const [source, setSource] = useState("Google");

    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [selectedBuyers, setSelectedBuyers] = useState([]);
    const [searchCount, setSearchCount] = useState(0);
    const [errorMessage, setErrorMessage] = useState("");

    const companiesFound = results.length;
    const emailsFound = results.filter((item) => item.email).length;
    const websitesFound = results.filter((item) => item.website).length;
    const statesFound = new Set(
        results.map((item) => item.state).filter(Boolean)
    ).size;

    const searchBuyers = async (event) => {
        event?.preventDefault();

        if (!product.trim()) {
            setErrorMessage("Please enter a product.");
            return;
        }

        if (!country.trim()) {
            setErrorMessage("Please enter a country.");
            return;
        }

        // Validate US ZIP only when the user actually entered one.
        if (country.trim().toLowerCase() === "usa" && zipCode.trim()) {
            const validZip = /^\d{5}(?:-\d{4})?$/.test(zipCode.trim());
            if (!validZip) {
                setErrorMessage(
                    "Invalid USA ZIP Code. Use 5 digits, for example 90012."
                );
                return;
            }
        }

        setLoading(true);
        setErrorMessage("");
        setResults([]);
        setSelectedBuyers([]);

        try {
            const params = {
                product: product.trim(),
                country: country.trim(),
                state: state.trim(),
                city: city.trim(),
                zip_code: zipCode.trim(),
                source: source.trim().toLowerCase(),
                limit: 50,
            };

            console.log("Buyer Search Request:", {
                url: `${API_BASE_URL}/api/search-buyers`,
                params,
            });

            const response = await buyerApi.get("/api/search-buyers", {
                params,
            });

            console.log("Buyer Search Response:", response.data);

            if (!response.data?.success) {
                throw new Error(
                    response.data?.message || "Buyer search failed."
                );
            }

            const buyers = Array.isArray(response.data.results)
                ? response.data.results.map((item, index) => ({
                      id:
                          item.id ||
                          item.website ||
                          `${item.company_name || item.company || "buyer"}-${index}`,
                      company_name:
                          item.company_name || item.company || "Unknown Company",
                      country: item.country || "",
                      state: item.state || "",
                      city: item.city || "",
                      zip_code: item.zip_code || item.zipcode || "",
                      website: item.website || "",
                      email: item.email || "",
                      phone: item.phone || "",
                      contact_person: item.contact_person || "",
                      buyer_type: item.buyer_type || "",
                      buyer_score: item.buyer_score || 0,
                  }))
                : [];

            setResults(buyers);
            setSearchCount((count) => count + 1);

            if (buyers.length === 0) {
                setErrorMessage(
                    "No verified buyers matched the selected location. Check the ZIP/City/State filters."
                );
            }
        } catch (error) {
            console.error("Buyer Search Error:", error);

            if (error.response) {
                setErrorMessage(
                    error.response.data?.message ||
                        `Backend returned HTTP ${error.response.status}.`
                );
            } else if (error.request) {
                setErrorMessage(
                    `Cannot reach Flask backend at ${API_BASE_URL}. Make sure python app.py is running on port 5000.`
                );
            } else {
                setErrorMessage(error.message || "Unable to search buyers.");
            }
        } finally {
            setLoading(false);
        }
    };

    const toggleBuyer = (buyer) => {
        setSelectedBuyers((current) => {
            const exists = current.some((item) => item.id === buyer.id);
            return exists
                ? current.filter((item) => item.id !== buyer.id)
                : [...current, buyer];
        });
    };

    const toggleSelectAll = () => {
        if (selectedBuyers.length === results.length) {
            setSelectedBuyers([]);
        } else {
            setSelectedBuyers([...results]);
        }
    };

    const saveSelectedBuyers = async () => {
        if (!selectedBuyers.length) {
            setErrorMessage("Please select at least one buyer.");
            return;
        }

        try {
            setErrorMessage("");

            for (const buyer of selectedBuyers) {
                await buyerApi.post("/api/buyers", {
                    company_name: buyer.company_name,
                    country: buyer.country,
                    state: buyer.state,
                    city: buyer.city,
                    zip_code: buyer.zip_code,
                    website: buyer.website,
                    email: buyer.email,
                    phone: buyer.phone,
                    contact_person: buyer.contact_person,
                });
            }

            alert(`${selectedBuyers.length} buyer(s) saved successfully.`);
            setSelectedBuyers([]);
        } catch (error) {
            console.error("Save Buyer Error:", error);
            setErrorMessage(
                error.response?.data?.message || "Failed to save buyers."
            );
        }
    };

    useEffect(() => {
        console.log(`Buyer Search page using API: ${API_BASE_URL}`);
    }, []);

    return (
        <Layout>
            <div className="space-y-8 pb-10">
                <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-700 p-8 text-white shadow-2xl">
                    <div className="relative flex flex-col lg:flex-row justify-between gap-8">
                        <div>
                            <div className="inline-flex items-center gap-2 bg-white/15 px-4 py-2 rounded-full mb-5">
                                <FaGlobe />
                                <span className="text-sm">Global Buyer Search</span>
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
                                    <p className="text-sm">Searches</p>
                                    <h2 className="text-4xl font-bold">
                                        {searchCount}
                                    </h2>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid lg:grid-cols-5 md:grid-cols-2 gap-6">
                    {[
                        ["Companies", companiesFound],
                        ["Websites", websitesFound],
                        ["Emails", emailsFound],
                        ["States", statesFound],
                        ["Selected", selectedBuyers.length],
                    ].map(([label, value]) => (
                        <div key={label} className="bg-white rounded-3xl shadow-lg p-6">
                            <p className="text-gray-500 text-sm">{label}</p>
                            <h2 className="text-4xl font-bold mt-3">{value}</h2>
                        </div>
                    ))}
                </div>

                <form
                    onSubmit={searchBuyers}
                    className="bg-white rounded-3xl shadow-xl border border-slate-200 p-8"
                >
                    <div className="flex items-center justify-between gap-4 mb-6">
                        <h2 className="text-3xl font-bold">Search Buyers</h2>
                        <span className="text-xs text-slate-500">
                            API: {API_BASE_URL}
                        </span>
                    </div>

                    {errorMessage && (
                        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                            {errorMessage}
                        </div>
                    )}

                    <div className="grid xl:grid-cols-7 lg:grid-cols-4 md:grid-cols-2 gap-5">
                        <Field label="Product">
                            <input
                                value={product}
                                onChange={(e) => setProduct(e.target.value)}
                                placeholder="Candles"
                                className="input"
                            />
                        </Field>

                        <Field label="Country">
                            <input
                                value={country}
                                onChange={(e) => setCountry(e.target.value)}
                                placeholder="USA"
                                className="input"
                            />
                        </Field>

                        <Field label="State">
                            <input
                                value={state}
                                onChange={(e) => setState(e.target.value)}
                                placeholder="California"
                                className="input"
                            />
                        </Field>

                        <Field label="City">
                            <input
                                value={city}
                                onChange={(e) => setCity(e.target.value)}
                                placeholder="Los Angeles"
                                className="input"
                            />
                        </Field>

                        <Field label="ZIP Code">
                            <input
                                value={zipCode}
                                onChange={(e) => setZipCode(e.target.value)}
                                placeholder="90012"
                                inputMode="numeric"
                                className="input"
                            />
                        </Field>

                        <Field label="Source">
                            <select
                                value={source}
                                onChange={(e) => setSource(e.target.value)}
                                className="input"
                            >
                                <option value="Google">Google</option>
                                <option value="Alibaba">Alibaba</option>
                                <option value="IndiaMART">IndiaMART</option>
                                <option value="TradeIndia">TradeIndia</option>
                                <option value="ExportersIndia">ExportersIndia</option>
                            </select>
                        </Field>

                        <div className="flex items-end">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 font-semibold shadow-lg hover:scale-[1.02] transition disabled:opacity-60 disabled:cursor-not-allowed"
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
                </form>

                <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5 px-8 py-6 border-b">
                        <div>
                            <h2 className="text-2xl font-bold">Search Results</h2>
                            <p className="text-gray-500 mt-2">
                                {results.length} buyers found
                            </p>
                        </div>

                        {results.length > 0 && (
                            <button
                                type="button"
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
                            <p className="mt-5 text-lg">Searching buyers...</p>
                        </div>
                    ) : results.length === 0 ? (
                        <div className="py-20 text-center">
                            <FaSearch className="mx-auto text-6xl text-gray-300" />
                            <p className="mt-5 text-gray-500">No buyers found.</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
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
                                    {results.map((buyer) => {
                                        const checked = selectedBuyers.some(
                                            (item) => item.id === buyer.id
                                        );

                                        return (
                                            <tr
                                                key={buyer.id}
                                                className="border-b hover:bg-slate-50"
                                            >
                                                <td className="px-4 py-4 text-center">
                                                    <input
                                                        type="checkbox"
                                                        checked={checked}
                                                        onChange={() => toggleBuyer(buyer)}
                                                    />
                                                </td>
                                                <td className="px-4 py-4">
                                                    <div className="flex items-center gap-2">
                                                        <FaBuilding className="text-blue-600 shrink-0" />
                                                        <span className="font-medium whitespace-nowrap">
                                                            {buyer.company_name}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-4">{buyer.country || "-"}</td>
                                                <td className="px-4 py-4">{buyer.state || "-"}</td>
                                                <td className="px-4 py-4">{buyer.city || "-"}</td>
                                                <td className="px-4 py-4">{buyer.zip_code || "-"}</td>
                                                <td className="px-4 py-4">
                                                    {buyer.website ? (
                                                        <a
                                                            href={buyer.website}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-blue-600 hover:underline whitespace-nowrap"
                                                        >
                                                            Visit Website
                                                        </a>
                                                    ) : (
                                                        "-"
                                                    )}
                                                </td>
                                                <td className="px-4 py-4">
                                                    {buyer.email ? (
                                                        <div className="flex items-center gap-2 whitespace-nowrap">
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

                {results.length > 0 && (
                    <div className="bg-white rounded-3xl shadow-xl border border-slate-200 p-8">
                        <div className="flex flex-col lg:flex-row justify-between items-center gap-6">
                            <div>
                                <h2 className="text-2xl font-bold">Buyer Summary</h2>
                                <p className="text-gray-500 mt-2">
                                    {selectedBuyers.length} buyer(s) selected
                                </p>
                            </div>

                            <div className="flex gap-4">
                                <button
                                    type="button"
                                    onClick={() => setSelectedBuyers([])}
                                    className="px-6 py-3 rounded-xl border border-gray-300 hover:bg-gray-100"
                                >
                                    Clear Selection
                                </button>
                                <button
                                    type="button"
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

            <style>{`
                .input {
                    width: 100%;
                    border-radius: 0.75rem;
                    border: 1px solid #cbd5e1;
                    padding: 0.75rem 1rem;
                    outline: none;
                    background: white;
                }
                .input:focus {
                    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
                    border-color: #3b82f6;
                }
            `}</style>
        </Layout>
    );
}

function Field({ label, children }) {
    return (
        <div>
            <label className="block text-sm font-semibold mb-2">{label}</label>
            {children}
        </div>
    );
}

export default BuyerSearch;
