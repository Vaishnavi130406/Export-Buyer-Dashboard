from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from models.buyer import Buyer

search_bp = Blueprint("search", __name__)


@search_bp.route("/api/search-buyers", methods=["POST"])
def search_buyers():

    data = request.get_json()

    keyword = data.get("keyword", "").strip()
    country = data.get("country", "").strip()

    query = Buyer.query

    if keyword:
        query = query.filter(
            Buyer.company_name.ilike(f"%{keyword}%")
        )

    if country:
        query = query.filter(
            Buyer.country.ilike(f"%{country}%")
        )

    buyers = query.all()

    return jsonify({
        "results": [
            {
                "id": buyer.id,
                "company_name": buyer.company_name,
                "country": buyer.country,
                "email": buyer.email
            }
            for buyer in buyers
        ]
    })