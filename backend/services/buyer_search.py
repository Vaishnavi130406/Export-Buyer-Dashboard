def search_buyers(keyword, country):

    sample_buyers = [

        {
            "company_name": "ABC Imports",
            "country": country,
            "email": "contact@abcimports.com"
        },

        {
            "company_name": "Global Furniture Ltd",
            "country": country,
            "email": "sales@globalfurniture.com"
        },

        {
            "company_name": "Premium Exporters",
            "country": country,
            "email": "info@premiumexporters.com"
        },

        {
            "company_name": f"{keyword} Trading Co.",
            "country": country,
            "email": "marketing@tradingco.com"
        }

    ]

    return sample_buyers