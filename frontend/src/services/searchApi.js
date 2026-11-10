import api from "./api";

export const searchBuyers = (product, country) => {
    return api.get("/api/search-buyers", {
        params: {
            product,
            country
        }
    });
};