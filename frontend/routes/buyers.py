from flask import Blueprint, jsonify, request
@buyers_bp.route("/api/buyers", methods=["POST"])
def add_buyer():

    data = request.json

    buyer = Buyer(
        name=data["name"],
        company=data["company"],
        country=data["country"],
        product=data["product"],
        email=data["email"],
        status=data["status"]
    )

    db.session.add(buyer)
    db.session.commit()

    return jsonify({"message": "Buyer added successfully"})