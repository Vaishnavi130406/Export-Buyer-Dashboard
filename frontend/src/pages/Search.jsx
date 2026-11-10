import { useState } from "react";
import Layout from "../components/Layout";
import api from "../services/api";

function Search() {

    const [keyword, setKeyword] = useState("");
    const [country, setCountry] = useState("");
    const [results, setResults] = useState([]);

    const searchBuyers = async () => {

        try {

            const res = await api.post("/api/search-buyers", {
                keyword,
                country
            });

            setResults(res.data.results);

        } catch (err) {

            console.log(err);

        }

    };

    return (

        <Layout>

            <h1>Buyer Search</h1>

            <br />

            <input
                type="text"
                placeholder="Product Keyword"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                style={{
                    width: "250px",
                    padding: "10px",
                    marginRight: "10px"
                }}
            />

            <input
                type="text"
                placeholder="Country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                style={{
                    width: "200px",
                    padding: "10px",
                    marginRight: "10px"
                }}
            />

            <button onClick={searchBuyers}>
                Search Buyers
            </button>

            <br /><br />

            <table border="1" cellPadding="10">

                <thead>

                    <tr>
                        <th>Buyer</th>
                        <th>Company</th>
                        <th>Country</th>
                        <th>Email</th>
                        <th>Website</th>
                    </tr>

                </thead>

                <tbody>

                    {results.map((buyer, index) => (

                        <tr key={index}>

                            <td>{buyer.buyer_name}</td>
                            <td>{buyer.company_name}</td>
                            <td>{buyer.country}</td>
                            <td>{buyer.email}</td>
                            <td>{buyer.website}</td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </Layout>

    );

}

export default Search;