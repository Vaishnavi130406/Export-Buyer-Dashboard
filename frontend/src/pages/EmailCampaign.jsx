import { useEffect, useState } from "react";

import Layout from "../components/Layout";
import api from "../services/api";

import {
    FaEnvelope,
    FaPaperPlane,
    FaUsers,
    FaGlobe,
    FaCheckCircle,
    FaSearch,
    FaBuilding,
} from "react-icons/fa";

function EmailCampaign() {

    // =====================================
    // State Variables
    // =====================================

    const [buyers, setBuyers] = useState([]);
    const [filteredBuyers, setFilteredBuyers] = useState([]);

    const [selectedBuyers, setSelectedBuyers] = useState([]);
    const [selectAll, setSelectAll] = useState(false);

    const [loading, setLoading] = useState(false);

    const [subject, setSubject] = useState("");
    const [message, setMessage] = useState("");

    const [search, setSearch] = useState("");

    const [attachment, setAttachment] = useState(null);

    const [campaignResult, setCampaignResult] = useState(null);

    // =====================================
    // Load Buyers
    // =====================================

    useEffect(() => {

        loadBuyers();

    }, []);

    // =====================================
    // Search Buyers
    // =====================================

    useEffect(() => {

        const keyword = search.toLowerCase();

        const result = buyers.filter((buyer) =>

            buyer.company_name
                .toLowerCase()
                .includes(keyword)

            ||

            buyer.country
                .toLowerCase()
                .includes(keyword)

            ||

            buyer.email
                .toLowerCase()
                .includes(keyword)

        );

        setFilteredBuyers(result);

    }, [buyers, search]);
    // =====================================
    // Load Buyers From Database
    // =====================================

    const loadBuyers = async () => {

        try {

            const res = await api.get("/api/buyers", {
                params: {
                    page: 1,
                    limit: 1000
                }
            });

            setBuyers(res.data.buyers);
            setFilteredBuyers(res.data.buyers);

        } catch (error) {

            console.log(error);

            alert("Unable to load buyers.");

        }

    };


    // =====================================
    // Toggle Buyer Selection
    // =====================================

    const toggleBuyer = (id) => {

        if (selectedBuyers.includes(id)) {

            setSelectedBuyers(
                selectedBuyers.filter(
                    buyerId => buyerId !== id
                )
            );

        } else {

            setSelectedBuyers([
                ...selectedBuyers,
                id
            ]);

        }

    };


    // =====================================
    // Select / Unselect All Buyers
    // =====================================

    const toggleSelectAll = () => {

        if (selectAll) {

            setSelectedBuyers([]);
            setSelectAll(false);

        } else {

            setSelectedBuyers(
                filteredBuyers.map(
                    buyer => buyer.id
                )
            );

            setSelectAll(true);

        }

    };


    // =====================================
    // PDF Attachment
    // =====================================

    const handleFileChange = (e) => {

        if (e.target.files.length > 0) {

            setAttachment(e.target.files[0]);

        }

    };


    // =====================================
    // Send Email Campaign
    // =====================================

    const sendCampaign = async () => {

        if (selectedBuyers.length === 0) {

            alert("Please select at least one buyer.");
            return;

        }

        if (!subject.trim()) {

            alert("Please enter email subject.");
            return;

        }

        if (!message.trim()) {

            alert("Please enter email message.");
            return;

        }

        try {

            setLoading(true);

            const formData = new FormData();

            formData.append("subject", subject);
            formData.append("message", message);

            formData.append(
                "buyer_ids",
                JSON.stringify(selectedBuyers)
            );

            if (attachment) {

                formData.append(
                    "attachment",
                    attachment
                );

            }
            const res = await api.post(

                "/api/email/send-campaign",

                formData,

                {

                    headers: {

                        "Content-Type": "multipart/form-data"

                    }

                }

            );

            setCampaignResult(res.data);

            alert("Campaign completed successfully.");

        }

        catch (error) {

            console.log(error);

            alert(

                error.response?.data?.error ||

                "Failed to send campaign."

            );

        }

        finally {

            setLoading(false);

        }

    };


    // =====================================
    // JSX
    // =====================================

    return (

        <Layout>

            <div className="space-y-6">


                {/* Header */}

                <div className="bg-gradient-to-r from-indigo-600 to-blue-700 rounded-2xl p-8 text-white shadow-lg">

                    <div className="flex items-center gap-4">

                        <div className="bg-white/20 p-4 rounded-xl">

                            <FaEnvelope className="text-3xl"/>

                        </div>

                        <div>

                            <h1 className="text-3xl font-bold">

                                Email Campaign

                            </h1>

                            <p className="text-blue-100 mt-2">

                                Send professional emails with PDF catalogue attachment.

                            </p>

                        </div>

                    </div>

                </div>


                {/* Statistics */}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                    <div className="bg-white rounded-2xl shadow p-6 flex items-center gap-4">

                        <div className="bg-blue-100 p-4 rounded-full">

                            <FaUsers className="text-blue-600 text-2xl"/>

                        </div>

                        <div>

                            <p className="text-gray-500 text-sm">

                                Total Buyers

                            </p>

                            <h2 className="text-3xl font-bold">

                                {buyers.length}

                            </h2>

                        </div>

                    </div>

                    <div className="bg-white rounded-2xl shadow p-6 flex items-center gap-4">

                        <div className="bg-green-100 p-4 rounded-full">

                            <FaCheckCircle className="text-green-600 text-2xl"/>

                        </div>

                        <div>

                            <p className="text-gray-500 text-sm">

                                Selected

                            </p>

                            <h2 className="text-3xl font-bold">

                                {selectedBuyers.length}

                            </h2>

                        </div>

                    </div>

                    <div className="bg-white rounded-2xl shadow p-6 flex items-center gap-4">

                        <div className="bg-purple-100 p-4 rounded-full">

                            <FaGlobe className="text-purple-600 text-2xl"/>

                        </div>

                        <div>

                            <p className="text-gray-500 text-sm">

                                Countries

                            </p>

                            <h2 className="text-3xl font-bold">

                                {

                                    new Set(

                                        buyers.map(

                                            b => b.country

                                        )

                                    ).size

                                }

                            </h2>

                        </div>

                    </div>

                </div>
                {/* Email Composer */}

                <div className="bg-white rounded-2xl shadow-md p-8">

                    <div className="flex items-center gap-3 mb-6">

                        <div className="bg-blue-100 p-3 rounded-xl">

                            <FaPaperPlane className="text-blue-600"/>

                        </div>

                        <h2 className="text-xl font-bold">

                            Compose Email

                        </h2>

                    </div>


                    <label className="font-semibold text-gray-700">

                        Email Subject

                    </label>

                    <input
                        type="text"
                        value={subject}
                        onChange={(e)=>setSubject(e.target.value)}
                        placeholder="Enter email subject"
                        className="w-full mt-2 mb-5 border rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
                    />


                    <label className="font-semibold text-gray-700">

                        Message

                    </label>

                    <textarea
                        rows="8"
                        value={message}
                        onChange={(e)=>setMessage(e.target.value)}
                        placeholder="Write your email..."
                        className="w-full mt-2 border rounded-xl px-4 py-3 resize-none outline-none focus:ring-2 focus:ring-blue-500"
                    />


                    <div className="mt-6">

                        <label className="font-semibold text-gray-700 block mb-2">

                            Attach PDF Catalogue

                        </label>

                        <input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="w-full border rounded-xl p-3"
                        />

                        {

                            attachment &&

                            <p className="mt-3 text-green-600 font-medium">

                                Selected:
                                {" "}
                                {attachment.name}

                            </p>

                        }

                    </div>

                </div>


                {/* Search */}

                <div className="bg-white rounded-2xl shadow-md p-6">

                    <div className="flex flex-col md:flex-row justify-between gap-4">

                        <div className="relative flex-1">

                            <FaSearch className="absolute left-4 top-4 text-gray-400"/>

                            <input
                                type="text"
                                placeholder="Search buyers..."
                                value={search}
                                onChange={(e)=>setSearch(e.target.value)}
                                className="w-full pl-12 py-3 border rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
                            />

                        </div>

                        <button
                            onClick={sendCampaign}
                            disabled={loading}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold flex items-center gap-2 disabled:bg-gray-400"
                        >

                            <FaPaperPlane/>

                            {

                                loading

                                ?

                                "Sending..."

                                :

                                "Send Campaign"

                            }

                        </button>

                    </div>

                </div>


                {/* Buyer Table */}

                <div className="bg-white rounded-2xl shadow-md overflow-hidden">

                    <div className="flex justify-between items-center p-6 border-b">

                        <div>

                            <h2 className="text-xl font-bold">

                                Select Buyers

                            </h2>

                            <p className="text-gray-500 text-sm">

                                Select recipients for this campaign.

                            </p>

                        </div>

                        <label className="flex items-center gap-2">

                            <input
                                type="checkbox"
                                checked={selectAll}
                                onChange={toggleSelectAll}
                            />

                            Select All

                        </label>

                    </div>


                    <div className="overflow-x-auto">

                        <table className="w-full">

                            <thead className="bg-gray-100">

                                <tr>

                                    <th className="px-6 py-4">

                                        Select

                                    </th>

                                    <th className="px-6 py-4">

                                        Company

                                    </th>

                                    <th className="px-6 py-4">

                                        Country

                                    </th>
                                    <th className="px-6 py-4">
    Email
</th>


                                </tr>

                            </thead>

                            <tbody>

                                {

                                    filteredBuyers.length === 0

                                    ?

                                    <tr>
                                        <td
    colSpan="4"
    className="text-center py-10 text-gray-500"
>

                                            No buyers found.

                                        </td>

                                    </tr>

                                    :

                                    filteredBuyers.map((buyer)=>(

                                        <tr
                                            key={buyer.id}
                                            className="border-t hover:bg-gray-50"
                                        >
                                            <td className="px-6 py-4">

                                                <input
                                                    type="checkbox"
                                                    checked={selectedBuyers.includes(buyer.id)}
                                                    onChange={() => toggleBuyer(buyer.id)}
                                                />

                                            </td>

                                            <td className="px-6 py-4">

                                                <div className="flex items-center gap-3">

                                                    <div className="bg-blue-100 p-2 rounded-lg">

                                                        <FaBuilding className="text-blue-600"/>

                                                    </div>

                                                    <span className="font-medium">

                                                        {buyer.company_name}

                                                    </span>

                                                </div>

                                            </td>

                                            <td className="px-6 py-4">

                                                <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm">

                                                    {buyer.country}

                                                </span>

                                            </td>

                                            <td className="px-6 py-4">

                                                <div className="flex items-center gap-2">

                                                    <FaEnvelope/>

                                                    {buyer.email}

                                                </div>

                                            </td>


                                        </tr>

                                    ))

                                }

                            </tbody>

                        </table>

                    </div>

                </div>


                {/* Campaign Result */}

                {

                    campaignResult &&

                    <div className="bg-green-50 border border-green-300 rounded-2xl p-8 shadow-md">

                        <div className="flex items-center gap-3 mb-6">

                            <div className="bg-green-100 p-3 rounded-full">

                                <FaCheckCircle className="text-green-600 text-2xl"/>

                            </div>

                            <h2 className="text-2xl font-bold text-green-700">

                                Campaign Completed

                            </h2>

                        </div>


                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

                            <div className="bg-white rounded-xl p-5 shadow">

                                <p className="text-gray-500">

                                    Recipients

                                </p>

                                <h3 className="text-3xl font-bold">

                                    {campaignResult.recipients}

                                </h3>

                            </div>


                            <div className="bg-white rounded-xl p-5 shadow">

                                <p className="text-gray-500">

                                    Sent

                                </p>

                                <h3 className="text-3xl font-bold text-green-600">

                                    {campaignResult.sent}

                                </h3>

                            </div>


                            <div className="bg-white rounded-xl p-5 shadow">

                                <p className="text-gray-500">

                                    Failed

                                </p>

                                <h3 className="text-3xl font-bold text-red-600">

                                    {campaignResult.failed}

                                </h3>

                            </div>

                        </div>


                        <div className="mt-6 bg-green-100 rounded-xl p-4 text-green-700 font-semibold">

                            ✓ Email campaign finished successfully.

                        </div>

                    </div>

                }

            </div>

        </Layout>

    );

}

export default EmailCampaign;