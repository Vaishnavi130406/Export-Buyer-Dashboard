import {
    FaChartPie,
    FaUsers,
    FaEnvelope,
    FaHistory,
    FaCog,
    FaGlobe,
    FaRocket,
    FaCircle,
    FaSearch,
    FaUserTie
} from "react-icons/fa";

import { NavLink } from "react-router-dom";

function Sidebar() {

    const menu = [

        // =========================================================
        // DASHBOARD
        // =========================================================

        {
            name: "Dashboard",
            icon: <FaChartPie />,
            path: "/dashboard"
        },


        // =========================================================
        // BUYER SEARCH
        // =========================================================

        {
            name: "Buyer Search",
            icon: <FaSearch />,
            path: "/buyer-search"
        },


        // =========================================================
        // BUYERS
        // =========================================================

        {
            name: "Buyers",
            icon: <FaUsers />,
            path: "/buyers"
        },


        // =========================================================
        // EMAIL CAMPAIGN
        // =========================================================

        {
            name: "Email Campaign",
            icon: <FaEnvelope />,
            path: "/campaign"
        },


        // =========================================================
        // EMAIL HISTORY
        // =========================================================

        {
            name: "Email History",
            icon: <FaHistory />,
            path: "/history"
        },


        // =========================================================
        // LEAD CRM
        // =========================================================

        {
            name: "Lead CRM",
            icon: <FaUsers />,
            path: "/lead-crm"
        },


        // =========================================================
        // TEAM REPORT - NEW
        // =========================================================

        {
            name: "Team Report",
            icon: <FaUserTie />,
            path: "/team-report"
        },


        // =========================================================
        // SETTINGS
        // =========================================================

        {
            name: "Settings",
            icon: <FaCog />,
            path: "/settings"
        }

    ];


    return (

        <aside className="w-72 min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white flex flex-col shadow-2xl">


            {/* =====================================================
                LOGO
            ====================================================== */}

            <div className="px-6 py-7 border-b border-slate-800">

                <div className="flex items-center gap-4">

                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">

                        <FaGlobe className="text-3xl" />

                    </div>


                    <div>

                        <h1 className="font-bold text-xl tracking-wide">
                            ExportPro
                        </h1>

                        <p className="text-xs text-slate-400 mt-1">
                            Buyer Automation System
                        </p>

                    </div>

                </div>

            </div>


            {/* =====================================================
                SYSTEM STATUS
            ====================================================== */}

            <div className="mx-5 mt-6 bg-slate-800/70 rounded-2xl p-4 border border-slate-700">

                <div className="flex items-center gap-3">

                    <div className="bg-green-500/20 p-2 rounded-lg">

                        <FaCircle className="text-green-400 text-xs" />

                    </div>


                    <div>

                        <p className="text-sm font-semibold">
                            System Online
                        </p>

                        <p className="text-xs text-slate-400">
                            All services running
                        </p>

                    </div>

                </div>

            </div>


            {/* =====================================================
                NAVIGATION
            ====================================================== */}

            <nav className="flex-1 px-4 mt-6 space-y-2">

                {menu.map((item) => (

                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `group flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-300 ${
                                isActive
                                    ? "bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg shadow-blue-900/40 text-white"
                                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                            }`
                        }
                    >

                        <span className="text-xl group-hover:scale-110 transition-transform">

                            {item.icon}

                        </span>


                        <span className="font-medium text-sm">

                            {item.name}

                        </span>

                    </NavLink>

                ))}

            </nav>


            {/* =====================================================
                QUICK ACTION
            ====================================================== */}

            <div className="mx-5 mb-5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-5 shadow-lg">

                <div className="flex items-center gap-3 mb-3">

                    <div className="bg-white/20 p-3 rounded-xl">

                        <FaRocket />

                    </div>

                    <h3 className="font-semibold">
                        Automation
                    </h3>

                </div>


                <p className="text-xs text-blue-100 leading-relaxed">

                    Manage buyers, discover new companies, and launch
                    email campaigns from one place.

                </p>

            </div>


            {/* =====================================================
                FOOTER
            ====================================================== */}

            <div className="border-t border-slate-800 px-6 py-5">

                <div className="flex justify-between items-center">

                    <p className="text-xs text-slate-500">
                        ExportPro Dashboard
                    </p>

                    <span className="bg-slate-800 px-3 py-1 rounded-full text-xs text-slate-400">
                        v1.0
                    </span>

                </div>

            </div>

        </aside>

    );

}

export default Sidebar;