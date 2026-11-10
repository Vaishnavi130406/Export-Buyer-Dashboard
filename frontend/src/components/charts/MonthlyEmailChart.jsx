import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend
} from "chart.js";

import api from "../../services/api";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend
);

function MonthlyEmailChart() {

    const [chartData, setChartData] = useState(null);

    useEffect(() => {
        fetchMonthlyEmails();
    }, []);

    const fetchMonthlyEmails = async () => {

        try {

            const response = await api.get("/api/dashboard/monthly");

            const data = response.data || [];

            setChartData({

                labels: data.map(item => item.month),

                datasets: [

                    {

                        label: "Emails Sent",

                        data: data.map(item => item.emails),

                        backgroundColor: "#3B82F6",

                        borderRadius: 8

                    }

                ]

            });

        } catch (error) {

            console.error(error);

        }

    };

    return (

        <div className="bg-white rounded-2xl shadow-lg border p-6">

            <h2 className="text-xl font-bold mb-5">

                📊 Monthly Email Activity

            </h2>

            <div className="h-80">

                {chartData ? (

                    <Bar
                        data={chartData}
                        options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: "bottom"
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }}
                    />

                ) : (

                    <div className="h-full flex items-center justify-center">

                        Loading...

                    </div>

                )}

            </div>

        </div>

    );

}

export default MonthlyEmailChart;