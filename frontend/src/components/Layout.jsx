import Sidebar from "./Sidebar";

function Layout({ children }) {

    return (

        <div className="flex min-h-screen bg-slate-100">

            {/* =====================================================
                SIDEBAR
            ====================================================== */}

            <Sidebar />


            {/* =====================================================
                MAIN CONTENT
            ====================================================== */}

            <main className="flex-1 flex flex-col">


                {/* =================================================
                    HEADER
                ================================================== */}

                <header className="bg-white shadow-sm border-b border-slate-200 px-10 py-5 flex justify-between items-center">

                    {/* Left Header */}

                    <div>

                        <h1 className="text-2xl font-bold text-slate-800">
                            Export Buyer Dashboard
                        </h1>

                        <p className="text-slate-500 mt-1">
                            Manage buyers and email campaigns
                        </p>

                    </div>


                    {/* Right Header - Team Leader */}

                    <div className="flex items-center gap-5">

                        <div className="hidden md:block text-right">

                            <p className="text-sm font-semibold text-slate-700">
                                Vaishnavi
                            </p>

                            <p className="text-xs text-blue-600 font-semibold">
                                Team Leader
                            </p>

                        </div>


                        {/* Profile Avatar */}

                        <div
                            className="
                                w-11
                                h-11
                                rounded-full
                                bg-gradient-to-r
                                from-blue-600
                                to-indigo-600
                                text-white
                                flex
                                items-center
                                justify-center
                                font-bold
                                shadow-lg
                            "
                        >
                            V
                        </div>

                    </div>

                </header>


                {/* =================================================
                    PAGE CONTENT
                ================================================== */}

                <div className="flex-1 p-8 overflow-auto">

                    {children}

                </div>

            </main>

        </div>
    );
}

export default Layout;