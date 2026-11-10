import { useEffect, useState } from "react";
import { Pie } from "react-chartjs-2";
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend
} from "chart.js";

import api from "../../services/api";

ChartJS.register(
    ArcElement,
    Tooltip,
    Legend
);

function BuyerCountryChart() {

    const [chartData, setChartData] = useState(null);

    useEffect(() => {
        fetchCountries();
    }, []);

    const fetchCountries = async () => {

        try {

            const response = await api.get(
                "/api/dashboard/countries"
            );

            const countries = response.data;

            setChartData({

                labels: countries.map(
                    item => item.country
                ),

                datasets: [

                    {

                        label: "Buyers",

                        data: countries.map(
                            item => item.buyers
                        ),

                        backgroundColor: [

                            "#3B82F6", // Blue
                            "#10B981", // Green
                            "#F59E0B", // Yellow
                            "#EF4444", // Red
                            "#8B5CF6", // Purple
                            "#06B6D4", // Cyan
                            "#EC4899", // Pink
                            "#F97316", // Orange
                            "#14B8A6", // Teal
                            "#6366F1"  // Indigo

                        ],

                        borderColor: "#FFFFFF",

                        borderWidth: 2,

                        hoverOffset: 18

                    }

                ]

            });

        } catch (error) {

            console.log(
                "Country Chart Error:",
                error
            );

        }

    };

    const options = {

        responsive: true,

        maintainAspectRatio: false,

        plugins: {

            legend: {

                position: "bottom",

                labels: {

                    padding: 20,

                    usePointStyle: true,

                    pointStyle: "circle",

                    font: {

                        size: 13

                    }

                }

            }

        }

    };

    return (

        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">

            <h2 className="text-xl font-bold text-gray-800 mb-5">

                🌍 Buyers By Country

            </h2>

            {

                chartData ?

                <div className="h-80">

                    <Pie
                        data={chartData}
                        options={options}
                    />

                </div>

                :

                <div className="h-80 flex items-center justify-center text-gray-500">

                    Loading chart...

                </div>

            }

        </div>

    );

}

export default BuyerCountryChart;