import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
    Filler
} from "chart.js";

import api from "../../services/api";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
    Filler
);

function EmailActivityChart() {

    const [chartData, setChartData] = useState(null);

    useEffect(() => {
        fetchEmailActivity();
    }, []);

    const fetchEmailActivity = async () => {

        try {

            const response = await api.get("/api/dashboard/emails");

            const data = response.data || [];

            setChartData({
                labels: data.map(item => item.date),
                datasets: [
                    {
                        label: "Emails Sent",
                        data: data.map(item => item.emails), // FIXED
                        borderColor: "#3B82F6",
                        backgroundColor: "rgba(59,130,246,0.2)",
                        fill: true,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7
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

                📈 Email Activity

            </h2>

            <div className="h-80">

                {chartData ? (

                    <Line
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

export default EmailActivityChart;