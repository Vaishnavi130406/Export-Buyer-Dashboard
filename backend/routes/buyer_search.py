from flask import Blueprint, jsonify, request

from services.buyer_search_service import search_buyers

buyer_search_bp = Blueprint("buyer_search", __name__)


@buyer_search_bp.route("/api/search-buyers", methods=["GET"])
def buyer_search():
    """Search buyers using BuyerSearch.jsx filters."""
    buyer = request.args.get("buyer", "").strip()
    product = request.args.get("product", "").strip()
    country = request.args.get("country", "").strip()
    state = request.args.get("state", "").strip()
    city = request.args.get("city", "").strip()
    zipcode = request.args.get(
        "zip_code",
        request.args.get("zipcode", ""),
    ).strip()
    source = request.args.get("source", "google").strip() or "google"

    raw_limit = request.args.get("limit", "50").strip()
    try:
        limit = max(1, min(int(raw_limit), 50))
    except (TypeError, ValueError):
        limit = 50

    if not product and not buyer:
        return jsonify({
            "success": False,
            "count": 0,
            "results": [],
            "message": "Please enter a product or buyer to search.",
        }), 400

    try:
        # Do NOT pass limit into search_buyers here.
        # This keeps the route compatible with both the older service
        # signature and the newer service signature.
        results = search_buyers(
            buyer=buyer,
            product=product,
            country=country,
            state=state,
            city=city,
            zipcode=zipcode,
            source=source,
        )

        results = (results or [])[:limit]

        return jsonify({
            "success": True,
            "count": len(results),
            "results": results,
            "filters": {
                "buyer": buyer,
                "product": product,
                "country": country,
                "state": state,
                "city": city,
                "zipcode": zipcode,
                "source": source,
                "limit": limit,
            },
        })

    except Exception as error:
        print("Buyer Search Error:", repr(error))
        return jsonify({
            "success": False,
            "count": 0,
            "results": [],
            "message": str(error),
        }), 500
