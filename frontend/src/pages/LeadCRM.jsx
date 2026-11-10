import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../services/api";

import {
    FaUsers,
    FaSearch,
    FaSpinner,
    FaEnvelope,
    FaClock,
    FaHandshake,
    FaCheckCircle,
    FaTimesCircle
} from "react-icons/fa";

function LeadCRM() {

    const [stats, setStats] = useState({
        total_buyers: 0,
        email_sent: 0,
        waiting_reply: 0,
        followup_due: 0,
        positive_reply: 0,
        negotiation: 0,
        closed_lead: 0,
        not_interested: 0
    });

    const [buyers, setBuyers] = useState([]);
    const [loading, setLoading] = useState(true);

    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("All");
    const [priority, setPriority] = useState("All");

    const [selectedBuyer, setSelectedBuyer] = useState(null);
    const [showEditModal, setShowEditModal] = useState(false);

    useEffect(() => {
        loadCRM();
    }, [search, status, priority]);

    async function loadCRM() {

        try {

            setLoading(true);

            const statsRes = await api.get("/api/crm/stats");

            setStats(statsRes.data.stats);

            const leadsRes = await api.get("/api/crm/leads", {
                params: {
                    search,
                    status,
                    priority
                }
            });

            setBuyers(leadsRes.data.buyers);

        } catch (err) {

            console.error(err);

            alert("Failed to load CRM data.");

        } finally {

            setLoading(false);

        }

    }

    async function saveLead() {

        try {

            await api.put(
                `/api/crm/update/${selectedBuyer.id}`,
                {
                    lead_status: selectedBuyer.lead_status,
                    priority: selectedBuyer.priority,
                    assigned_to: selectedBuyer.assigned_to,
                    notes: selectedBuyer.notes,
                    followup_date: selectedBuyer.followup_date
                }
            );

            alert("Lead Updated Successfully!");

            setShowEditModal(false);

            loadCRM();

        } catch (err) {

            console.error(err);

            alert("Unable to update lead.");

        }

    }

    function openEditModal(buyer) {

        setSelectedBuyer({
            ...buyer
        });

        setShowEditModal(true);

    }

    function getStatusColor(status) {

        switch (status) {

            case "Email Sent":
                return "bg-blue-100 text-blue-700";

            case "Waiting Reply":
                return "bg-yellow-100 text-yellow-700";

            case "Follow-up Due":
                return "bg-orange-100 text-orange-700";

            case "Positive Reply":
                return "bg-green-100 text-green-700";

            case "Negotiation":
                return "bg-purple-100 text-purple-700";

            case "Closed Lead":
                return "bg-emerald-100 text-emerald-700";

            case "Not Interested":
                return "bg-red-100 text-red-700";

            default:
                return "bg-gray-100 text-gray-700";
        }

    }

    return (

        <Layout>

            <div className="p-8">

                <div className="mb-8">

                    <h1 className="text-3xl font-bold text-gray-800">
                        Lead Management CRM
                    </h1>

                    <p className="text-gray-500 mt-2">
                        Manage buyers, leads and follow-ups professionally
                    </p>

                </div>
{/* ===================== Statistics ===================== */}

<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

    <StatCard
        title="Total Buyers"
        value={stats.total_buyers}
        color="bg-blue-500"
        icon={<FaUsers />}
    />

    <StatCard
        title="Email Sent"
        value={stats.email_sent}
        color="bg-indigo-500"
        icon={<FaEnvelope />}
    />

    <StatCard
        title="Waiting Reply"
        value={stats.waiting_reply}
        color="bg-yellow-500"
        icon={<FaClock />}
    />

    <StatCard
        title="Follow-up Due"
        value={stats.followup_due}
        color="bg-orange-500"
        icon={<FaClock />}
    />

    <StatCard
        title="Positive Reply"
        value={stats.positive_reply}
        color="bg-green-500"
        icon={<FaCheckCircle />}
    />

    <StatCard
        title="Negotiation"
        value={stats.negotiation}
        color="bg-purple-500"
        icon={<FaHandshake />}
    />

    <StatCard
        title="Closed Lead"
        value={stats.closed_lead}
        color="bg-emerald-600"
        icon={<FaCheckCircle />}
    />

    <StatCard
        title="Rejected"
        value={stats.not_interested}
        color="bg-red-500"
        icon={<FaTimesCircle />}
    />

</div>

{/* ===================== Search ===================== */}

<div className="bg-white rounded-xl shadow mt-8 p-6">

    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        <div className="relative">

            <FaSearch className="absolute left-3 top-3 text-gray-400" />

            <input
                type="text"
                placeholder="Search Company..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full border rounded-lg pl-10 pr-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
            />

        </div>

        <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="border rounded-lg px-4 py-2"
        >

            <option>All</option>
            <option>Email Sent</option>
            <option>Waiting Reply</option>
            <option>Follow-up Due</option>
            <option>Positive Reply</option>
            <option>Negotiation</option>
            <option>Closed Lead</option>
            <option>Not Interested</option>

        </select>

        <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="border rounded-lg px-4 py-2"
        >

            <option>All</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>

        </select>

    </div>

</div>

{/* ===================== Loading ===================== */}

{loading && (

<div className="flex justify-center mt-10">

    <FaSpinner className="animate-spin text-blue-600 text-4xl" />

</div>

)}

{/* ===================== Table ===================== */}

{!loading && buyers.length > 0 && (

<div className="bg-white rounded-xl shadow mt-8 overflow-x-auto">

<table className="min-w-full">

<thead className="bg-gray-100">

<tr>

<th className="px-6 py-3 text-left">Company</th>
<th className="px-6 py-3 text-left">Country</th>
<th className="px-6 py-3 text-left">Email</th>
<th className="px-6 py-3 text-left">Status</th>
<th className="px-6 py-3 text-left">Priority</th>
<th className="px-6 py-3 text-left">Assigned</th>
<th className="px-6 py-3 text-left">Follow-up</th>
<th className="px-6 py-3 text-center">Actions</th>

</tr>

</thead>

<tbody>

{buyers.map((buyer) => (

<tr
    key={buyer.id}
    className="border-t hover:bg-gray-50 transition"
>

<td className="px-6 py-4 font-semibold">
    {buyer.company_name}
</td>

<td className="px-6 py-4">
    {buyer.country}
</td>

<td className="px-6 py-4">
    {buyer.email}
</td>

<td className="px-6 py-4">

<span
className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(
buyer.lead_status
)}`}
>

{buyer.lead_status}

</span>

</td>

<td className="px-6 py-4">
    {buyer.priority}
</td>

<td className="px-6 py-4">
    {buyer.assigned_to}
</td>

<td className="px-6 py-4">
    {buyer.followup_date || "-"}
</td>

<td className="px-6 py-4">

<div className="flex justify-center gap-2">

<button
className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
onClick={() => {

alert(

`Company : ${buyer.company_name}

Country : ${buyer.country}

Email : ${buyer.email}

Status : ${buyer.lead_status}

Priority : ${buyer.priority}

Assigned To : ${buyer.assigned_to}

Notes : ${buyer.notes || "No Notes"}`

);

}}
>

View

</button>

<button
className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded"
onClick={() => openEditModal(buyer)}
>

Edit

</button>

</div>

</td>

</tr>

))}

</tbody>

</table>

</div>

)}

{!loading && buyers.length === 0 && (

<div className="bg-white shadow rounded-xl mt-8 p-12 text-center">

<h2 className="text-2xl font-bold">

No Leads Found

</h2>

<p className="text-gray-500 mt-2">

Try another search.

</p>

</div>

)}
{/* ===================== EDIT MODAL ===================== */}

{showEditModal && selectedBuyer && (

<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">

<div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-8">

<div className="flex justify-between items-center mb-6">

<h2 className="text-2xl font-bold">

Edit Lead

</h2>

<button
onClick={() => setShowEditModal(false)}
className="text-3xl text-gray-500 hover:text-red-500"
>

×

</button>

</div>

<div className="grid grid-cols-1 md:grid-cols-2 gap-5">

<div>

<label className="block font-semibold mb-2">

Company

</label>

<input
type="text"
value={selectedBuyer.company_name}
disabled
className="w-full border rounded-lg px-4 py-2 bg-gray-100"
/>

</div>

<div>

<label className="block font-semibold mb-2">

Email

</label>

<input
type="email"
value={selectedBuyer.email}
disabled
className="w-full border rounded-lg px-4 py-2 bg-gray-100"
/>

</div>

<div>

<label className="block font-semibold mb-2">

Lead Status

</label>

<select
value={selectedBuyer.lead_status}
onChange={(e)=>

setSelectedBuyer({

...selectedBuyer,

lead_status:e.target.value

})

}
className="w-full border rounded-lg px-4 py-2"
>

<option>Email Sent</option>

<option>Waiting Reply</option>

<option>Follow-up Due</option>

<option>Positive Reply</option>

<option>Negotiation</option>

<option>Closed Lead</option>

<option>Not Interested</option>

</select>

</div>

<div>

<label className="block font-semibold mb-2">

Priority

</label>

<select
value={selectedBuyer.priority}
onChange={(e)=>

setSelectedBuyer({

...selectedBuyer,

priority:e.target.value

})

}
className="w-full border rounded-lg px-4 py-2"
>

<option>High</option>

<option>Medium</option>

<option>Low</option>

</select>

</div>

<div className="md:col-span-2">

<label className="block font-semibold mb-2">

Assigned To

</label>

<input
type="text"
value={selectedBuyer.assigned_to}
onChange={(e)=>

setSelectedBuyer({

...selectedBuyer,

assigned_to:e.target.value

})

}
className="w-full border rounded-lg px-4 py-2"
/>

</div>

<div className="md:col-span-2">

<label className="block font-semibold mb-2">

Follow-up Date

</label>

<input
type="date"
value={selectedBuyer.followup_date || ""}
onChange={(e)=>

setSelectedBuyer({

...selectedBuyer,

followup_date:e.target.value

})

}
className="w-full border rounded-lg px-4 py-2"
/>

</div>

<div className="md:col-span-2">

<label className="block font-semibold mb-2">

Notes

</label>

<textarea
rows="5"
value={selectedBuyer.notes || ""}
onChange={(e)=>

setSelectedBuyer({

...selectedBuyer,

notes:e.target.value

})

}
className="w-full border rounded-lg px-4 py-2 resize-none"
/>

</div>
        </div>

        {/* Action Buttons */}

        <div className="flex justify-end gap-4 mt-8">

            <button
                onClick={() => setShowEditModal(false)}
                className="px-5 py-2 rounded-lg bg-gray-200 hover:bg-gray-300"
            >
                Cancel
            </button>

            <button
                onClick={saveLead}
                className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold"
            >
                Save Changes
            </button>

        </div>

    </div>

</div>

)}

            </div>

        </Layout>

    );

}

function StatCard({

    title,

    value,

    color,

    icon

}) {

    return (

        <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition p-5 flex items-center justify-between">

            <div>

                <p className="text-gray-500 text-sm">

                    {title}

                </p>

                <h2 className="text-3xl font-bold mt-2">

                    {value}

                </h2>

            </div>

            <div className={`${color} text-white text-3xl p-4 rounded-xl`}>

                {icon}

            </div>

        </div>

    );

}

export default LeadCRM;