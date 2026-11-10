import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../services/api";

import BuyerCountryChart from "../components/charts/BuyerCountryChart";
import EmailActivityChart from "../components/charts/EmailActivityChart";
import MonthlyEmailChart from "../components/charts/MonthlyEmailChart";
import {
    FaUsers,
    FaEnvelope,
    FaMagnifyingGlass,
    FaClock,
    FaArrowTrendUp
} from "react-icons/fa6";

function Dashboard() {

    const [stats, setStats] = useState({

        total_buyers: 0,
        emails_sent: 0,
        today_searches: 0,
        pending_emails: 0

    });

    useEffect(() => {

        fetchDashboard();

    }, []);

    const fetchDashboard = async () => {

        try {

            const response = await api.get("/api/dashboard");

            setStats(response.data);

        }

        catch (error) {

            console.log(error);

        }

    };

    return (

        <Layout>

            <div className="min-h-screen bg-slate-100 p-8">

                {/* Header */}

                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8">

                    <div>

                        <h1 className="text-4xl font-bold text-slate-800">

                            Dashboard

                        </h1>

                        <p className="text-slate-500 mt-2">

                            Welcome back! Here's your Export Buyer Dashboard overview.

                        </p>

                    </div>

                    <div className="mt-5 lg:mt-0">

                        <div className="bg-white rounded-xl shadow px-5 py-3">

                            <p className="text-sm text-gray-500">

                                System Status

                            </p>

                            <p className="text-green-600 font-bold">

                                ● Online

                            </p>

                        </div>

                    </div>

                </div>

                {/* Statistics */}

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">

                    {/* Buyers */}

                    <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between">

                            <div>

                                <p className="text-blue-100">

                                    Total Buyers

                                </p>

                                <h2 className="text-4xl font-bold mt-3">

                                    {stats.total_buyers}

                                </h2>

                            </div>

                            <FaUsers size={42} />

                        </div>

                    </div>

                    {/* Emails */}

                    <div className="bg-gradient-to-r from-green-600 to-green-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between">

                            <div>

                                <p className="text-green-100">

                                    Emails Sent

                                </p>

                                <h2 className="text-4xl font-bold mt-3">

                                    {stats.emails_sent}

                                </h2>

                            </div>

                            <FaEnvelope size={42} />

                        </div>

                    </div>

                    {/* Searches */}

                    <div className="bg-gradient-to-r from-purple-600 to-purple-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between">

                            <div>

                                <p className="text-purple-100">

                                    Today's Searches

                                </p>

                                <h2 className="text-4xl font-bold mt-3">

                                    {stats.today_searches}

                                </h2>

                            </div>

                            <FaMagnifyingGlass size={42} />

                        </div>

                    </div>

                    {/* Pending */}

                    <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl shadow-lg text-white p-6">

                        <div className="flex justify-between">

                            <div>

                                <p className="text-orange-100">

                                    Pending Emails

                                </p>

                                <h2 className="text-4xl font-bold mt-3">

                                    {stats.pending_emails}

                                </h2>

                            </div>

                            <FaClock size={42} />

                        </div>

                    </div>

                </div>

                {/* Analytics */}

                <div className="mt-10 grid grid-cols-1 xl:grid-cols-3 gap-6">

                    <div className="xl:col-span-2">

                        <BuyerCountryChart />

                    </div>

                    <div className="bg-white rounded-2xl shadow-lg p-6">

                        <div className="flex items-center gap-3 mb-4">

                            <FaArrowTrendUp className="text-blue-600 text-xl" />

                            <h2 className="text-xl font-bold text-slate-700">

                                Quick Overview

                            </h2>

                        </div>

                        <div className="space-y-5">

                            <div className="flex justify-between">

                                <span className="text-gray-600">

                                    Registered Buyers

                                </span>

                                <span className="font-bold text-blue-600">

                                    {stats.total_buyers}

                                </span>

                            </div>

                            <div className="flex justify-between">

                                <span className="text-gray-600">

                                    Emails Delivered

                                </span>

                                <span className="font-bold text-green-600">

                                    {stats.emails_sent}

                                </span>

                            </div>

                            <div className="flex justify-between">

                                <span className="text-gray-600">

                                    Searches Today

                                </span>

                                <span className="font-bold text-purple-600">

                                    {stats.today_searches}

                                </span>

                            </div>

                            <div className="flex justify-between">

                                <span className="text-gray-600">

                                    Pending Campaigns

                                </span>

                                <span className="font-bold text-red-500">

                                    {stats.pending_emails}

                                </span>

                            </div>

                            <hr />

                            <div>

                                <p className="text-gray-500 text-sm">

                                    Export Buyer Dashboard helps you manage buyers,
                                    email campaigns, analytics and export operations
                                    from one centralized platform.

                                </p>

                            </div>

                        </div>

                    </div>

                </div>

                {/* Charts */}

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-8">

                    <EmailActivityChart />

                    <MonthlyEmailChart />

                </div>

            </div>

        </Layout>

    );

}

export default Dashboard;