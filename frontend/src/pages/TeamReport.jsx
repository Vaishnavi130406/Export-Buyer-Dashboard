import Layout from "../components/Layout";

import {
    FaUsers,
    FaEnvelope,
    FaRobot,
    FaThumbsUp,
    FaUserTie
} from "react-icons/fa6";

function TeamReport() {

    // =========================================================
    // TEAM REPORT DATA
    // =========================================================

    const teamMembers = [
        {
            name: "Vaishnavi",
            role: "Team Leader",
            emailsSent: 1875,
            automatedResponses: 17,
            positiveResponses: 4,
            isLeader: true
        },
        {
            name: "Dakshta Methwani",
            role: "Member",
            emailsSent: 914,
            automatedResponses: 14,
            positiveResponses: 0
        },
        {
            name: "Shivendra Parihar",
            role: "Member",
            emailsSent: 461,
            automatedResponses: 16,
            positiveResponses: 1
        },
        {
            name: "Gauranshi Varshney",
            role: "Member",
            emailsSent: 263,
            automatedResponses: 3,
            positiveResponses: 1
        },
        {
            name: "Arth Patel",
            role: "Member",
            emailsSent: 445,
            automatedResponses: 15,
            positiveResponses: 0
        },
        {
            name: "Chiviti Ajay",
            role: "Member",
            emailsSent: 471,
            automatedResponses: 3,
            positiveResponses: 0
        },
        {
            name: "Prajwal Rai",
            role: "Member",
            emailsSent: 64,
            automatedResponses: 0,
            positiveResponses: 2
        },
        {
            name: "Putluri Vasanthi",
            role: "Member",
            emailsSent: 63,
            automatedResponses: 2,
            positiveResponses: 0
        },
        {
            name: "Tuhin Mondal",
            role: "Member",
            emailsSent: 98,
            automatedResponses: 2,
            positiveResponses: 0
        },
        {
            name: "Ritik Pal",
            role: "Member",
            emailsSent: 94,
            automatedResponses: 0,
            positiveResponses: 0
        },
        {
            name: "Sindhuja",
            role: "Member",
            emailsSent: 61,
            automatedResponses: 0,
            positiveResponses: 0
        },
        {
            name: "Madhu",
            role: "Member",
            emailsSent: 117,
            automatedResponses: 2,
            positiveResponses: 0
        },
        {
            name: "Chaitanya",
            role: "Member",
            emailsSent: 58,
            automatedResponses: 0,
            positiveResponses: 0
        },
        
        {
            name: "Subhanshu Pal",
            role: "Member",
            emailsSent: 60,
            automatedResponses: 0,
            positiveResponses: 0
        }
    ];

    // =========================================================
    // TOTALS OF REPORTED DATA
    // =========================================================

    const totalEmailsSent = teamMembers.reduce(
        (total, member) =>
            total + (member.emailsSent ?? 0),
        0
    );

    const totalAutomatedResponses = teamMembers.reduce(
        (total, member) =>
            total + (member.automatedResponses ?? 0),
        0
    );

    const totalPositiveResponses = teamMembers.reduce(
        (total, member) =>
            total + (member.positiveResponses ?? 0),
        0
    );

    return (
        <Layout>

            <div className="min-h-screen bg-slate-100 p-8">

                {/* =====================================================
                    HEADER
                ====================================================== */}

                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8">

                    <div>

                        <h1 className="text-4xl font-bold text-slate-800">
                            Team Report
                        </h1>

                        <p className="text-slate-500 mt-2">
                            Team email outreach and response performance
                        </p>

                    </div>

                    <div className="mt-5 lg:mt-0">

                        <div className="bg-white rounded-xl shadow px-5 py-3">

                            <p className="text-sm text-gray-500">
                                Total Team
                            </p>

                            <p className="text-blue-600 font-bold text-xl">
                                {teamMembers.length} Members
                            </p>

                        </div>

                    </div>

                </div>


                {/* =====================================================
                    SUMMARY CARDS
                ====================================================== */}

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">

                    {/* Team Members */}

                    <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between items-center">

                            <div>

                                <p className="text-blue-100">
                                    Team Members
                                </p>

                                <h2 className="text-4xl font-bold mt-3">
                                    {teamMembers.length}
                                </h2>

                            </div>

                            <FaUsers size={40} />

                        </div>

                    </div>


                    {/* Emails Sent */}

                    <div className="bg-gradient-to-r from-green-600 to-green-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between items-center">

                            <div>

                                <p className="text-green-100">
                                    Emails Sent
                                </p>

                                <h2 className="text-4xl font-bold mt-3">
                                    {totalEmailsSent.toLocaleString()}
                                </h2>

                            </div>

                            <FaEnvelope size={40} />

                        </div>

                    </div>


                    {/* Automated Responses */}

                    <div className="bg-gradient-to-r from-purple-600 to-purple-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between items-center">

                            <div>

                                <p className="text-purple-100">
                                    Automated Responses
                                </p>

                                <h2 className="text-4xl font-bold mt-3">
                                    {totalAutomatedResponses.toLocaleString()}
                                </h2>

                            </div>

                            <FaRobot size={40} />

                        </div>

                    </div>


                    {/* Positive Responses */}

                    <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between items-center">

                            <div>

                                <p className="text-orange-100">
                                    Positive Responses
                                </p>

                                <h2 className="text-4xl font-bold mt-3">
                                    {totalPositiveResponses.toLocaleString()}
                                </h2>

                            </div>

                            <FaThumbsUp size={40} />

                        </div>

                    </div>

                </div>


                {/* =====================================================
                    TEAM LEADER CARD
                ====================================================== */}

                <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-8">

                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">

                        <div className="flex items-center gap-4">

                            <div className="w-16 h-16 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">

                                <FaUserTie size={30} />

                            </div>

                            <div>

                                <p className="text-sm text-gray-500">
                                    Team Leader
                                </p>

                                <h2 className="text-2xl font-bold text-slate-800">
                                    Vaishnavi
                                </h2>

                            </div>

                        </div>


                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full md:w-auto">

                            <div className="bg-slate-50 rounded-xl px-6 py-4">

                                <p className="text-xs text-gray-500">
                                    Emails Sent
                                </p>

                                <p className="text-xl font-bold text-green-600">
                                    1,875
                                </p>

                            </div>


                            <div className="bg-slate-50 rounded-xl px-6 py-4">

                                <p className="text-xs text-gray-500">
                                    Automated Responses
                                </p>

                                <p className="text-xl font-bold text-purple-600">
                                    17
                                </p>

                            </div>


                            <div className="bg-slate-50 rounded-xl px-6 py-4">

                                <p className="text-xs text-gray-500">
                                    Positive Responses
                                </p>

                                <p className="text-xl font-bold text-orange-600">
                                    3
                                </p>

                            </div>

                        </div>

                    </div>

                </div>


                {/* =====================================================
                    TEAM MEMBERS TABLE
                ====================================================== */}

                <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">

                    {/* Table Header */}

                    <div className="px-6 py-5 border-b border-slate-200">

                        <h2 className="text-2xl font-bold text-slate-800">
                            Team Members Report
                        </h2>

                        <p className="text-slate-500 text-sm mt-1">
                            Individual email activity and response data
                        </p>

                    </div>


                    {/* Responsive Table */}

                    <div className="overflow-x-auto">

                        <table className="min-w-full">

                            <thead className="bg-slate-50">

                                <tr>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        #
                                    </th>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        Team Member
                                    </th>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        Role
                                    </th>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        Emails Sent
                                    </th>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        Automated Responses
                                    </th>

                                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-600">
                                        Positive Responses
                                    </th>

                                </tr>

                            </thead>


                            <tbody className="divide-y divide-slate-200">

                                {teamMembers.map((member, index) => (

                                    <tr
                                        key={member.name}
                                        className={`transition ${
                                            member.isLeader
                                                ? "bg-blue-50 hover:bg-blue-100"
                                                : "hover:bg-slate-50"
                                        }`}
                                    >

                                        {/* Number */}

                                        <td className="px-6 py-5 text-sm text-slate-500">
                                            {index + 1}
                                        </td>


                                        {/* Name */}

                                        <td className="px-6 py-5">

                                            <div className="flex items-center gap-3">

                                                <div
                                                    className={`w-11 h-11 rounded-full flex items-center justify-center font-bold ${
                                                        member.isLeader
                                                            ? "bg-blue-600 text-white"
                                                            : "bg-slate-200 text-slate-700"
                                                    }`}
                                                >
                                                    {member.name
                                                        .split(" ")
                                                        .map((word) => word[0])
                                                        .join("")
                                                        .substring(0, 2)
                                                        .toUpperCase()}
                                                </div>

                                                <div>

                                                    <p className="font-semibold text-slate-800">
                                                        {member.name}
                                                    </p>

                                                    {member.isLeader && (
                                                        <span className="text-xs font-semibold text-blue-600">
                                                            Team Leader
                                                        </span>
                                                    )}

                                                </div>

                                            </div>

                                        </td>


                                        {/* Role */}

                                        <td className="px-6 py-5">

                                            {member.isLeader ? (

                                                <span className="inline-flex px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">
                                                    Team Leader
                                                </span>

                                            ) : (

                                                <span className="inline-flex px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-sm font-medium">
                                                    Member
                                                </span>

                                            )}

                                        </td>


                                        {/* Emails Sent */}

                                        <td className="px-6 py-5">

                                            <span className="font-bold text-slate-800">

                                                {member.emailsSent !== null
                                                    ? member.emailsSent.toLocaleString()
                                                    : "—"}

                                            </span>

                                        </td>


                                        {/* Automated Responses */}

                                        <td className="px-6 py-5">

                                            {member.automatedResponses !== null ? (

                                                <span className="inline-flex items-center px-3 py-1 rounded-full bg-purple-100 text-purple-700 font-semibold">

                                                    {member.automatedResponses}

                                                </span>

                                            ) : (

                                                <span className="text-gray-400">
                                                    —
                                                </span>

                                            )}

                                        </td>


                                        {/* Positive Responses */}

                                        <td className="px-6 py-5">

                                            {member.positiveResponses !== null ? (

                                                <span className="inline-flex items-center px-3 py-1 rounded-full bg-green-100 text-green-700 font-semibold">

                                                    {member.positiveResponses}

                                                </span>

                                            ) : (

                                                <span className="text-gray-400">
                                                    —
                                                </span>

                                            )}

                                        </td>

                                    </tr>

                                ))}

                            </tbody>

                        </table>

                    </div>


                    {/* =================================================
                        FOOTER NOTE
                    ================================================== */}

                    <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">

                        <p className="text-sm text-slate-500">

                            <span className="font-semibold">
                                Note:
                            </span>{" "}
                            A dash (—) means the report for that member has
                            not been entered yet.

                        </p>

                    </div>

                </div>

            </div>

        </Layout>
    );
}

export default TeamReport;