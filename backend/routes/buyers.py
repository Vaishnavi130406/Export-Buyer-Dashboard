from flask import Blueprint, jsonify, request, send_file
import csv
import io

from sqlalchemy import or_, asc, desc
from sqlalchemy.exc import IntegrityError

from models import db
from models.buyer import Buyer


buyers_bp = Blueprint("buyers", __name__)


# ==========================================
# GET ALL BUYERS
# Search + Pagination + Sorting
# ==========================================

@buyers_bp.route("/api/buyers", methods=["GET"])
def get_buyers():

    search = request.args.get(
        "search",
        ""
    ).strip()

    page = int(
        request.args.get(
            "page",
            1
        )
    )

    per_page = int(
        request.args.get(
            "limit",
            10
        )
    )

    sort_by = request.args.get(
        "sort",
        "company_name"
    )

    order = request.args.get(
        "order",
        "asc"
    )

    query = Buyer.query

    # Search Filter
    if search:

        query = query.filter(

            or_(

                Buyer.company_name.ilike(
                    f"%{search}%"
                ),

                Buyer.country.ilike(
                    f"%{search}%"
                ),

                Buyer.email.ilike(
                    f"%{search}%"
                )

            )

        )

    # Sorting
    if hasattr(Buyer, sort_by):

        column = getattr(
            Buyer,
            sort_by
        )

        if order == "desc":

            query = query.order_by(
                desc(column)
            )

        else:

            query = query.order_by(
                asc(column)
            )

    # Pagination
    pagination = query.paginate(

        page=page,

        per_page=per_page,

        error_out=False

    )

    return jsonify({

        "buyers": [

            buyer.to_dict()

            for buyer in pagination.items

        ],

        "current_page": page,

        "total_pages": pagination.pages,

        "total_buyers": pagination.total

    })


# ==========================================
# ADD NEW BUYER
# ==========================================

@buyers_bp.route("/api/buyers", methods=["POST"])
def add_buyer():

    data = request.get_json()

    company_name = (
        data.get("company_name", "")
        .strip()
    )

    country = (
        data.get("country", "")
        .strip()
    )

    email = (
        data.get("email", "")
        .strip()
        .lower()
    )

    website = (
        data.get("website", "")
        .strip()
        .lower()
    )

    if not company_name:

        return jsonify({

            "success": False,

            "message": "Company name is required."

        }), 400

    if not email:

        return jsonify({

            "success": False,

            "message": "Email is required."

        }), 400

    # ------------------------------------
    # Check duplicate email
    # ------------------------------------

    existing = Buyer.query.filter_by(
        email=email
    ).first()

    if existing:

        return jsonify({

            "success": True,

            "message": "Buyer already exists.",

            "buyer": existing.to_dict()

        }), 200

    buyer = Buyer(

        company_name=company_name,

        country=country,

        email=email

    )

    try:

        db.session.add(buyer)

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Buyer added successfully.",

            "buyer": buyer.to_dict()

        }), 201

    except IntegrityError:

        db.session.rollback()

        existing = Buyer.query.filter_by(
            email=email
        ).first()

        return jsonify({

            "success": True,

            "message": "Buyer already exists.",

            "buyer": existing.to_dict() if existing else None

        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500
# ==========================================
# UPDATE BUYER
# ==========================================

@buyers_bp.route(
    "/api/buyers/<int:id>",
    methods=["PUT"]
)
def update_buyer(id):

    buyer = Buyer.query.get_or_404(id)

    data = request.get_json()

    company_name = data.get(
        "company_name",
        buyer.company_name
    ).strip()

    country = data.get(
        "country",
        buyer.country
    ).strip()

    email = data.get(
        "email",
        buyer.email
    ).strip().lower()

    # ------------------------------------------
    # Duplicate email check
    # ------------------------------------------

    duplicate = Buyer.query.filter(
        Buyer.email == email,
        Buyer.id != id
    ).first()

    if duplicate:

        return jsonify({

            "success": False,

            "message": "Another buyer already uses this email."

        }), 400

    buyer.company_name = company_name
    buyer.country = country
    buyer.email = email

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Buyer updated successfully.",

            "buyer": buyer.to_dict()

        })

    except IntegrityError:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": "Duplicate email found."

        }), 400

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================
# DELETE BUYER
# ==========================================

@buyers_bp.route(
    "/api/buyers/<int:id>",
    methods=["DELETE"]
)
def delete_buyer(id):

    buyer = Buyer.query.get_or_404(id)

    try:

        db.session.delete(buyer)

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Buyer deleted successfully."

        })

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# ==========================================
# EXPORT BUYERS CSV
# ==========================================

@buyers_bp.route(
    "/api/buyers/export",
    methods=["GET"]
)
def export_buyers():

    buyers = Buyer.query.order_by(

        Buyer.company_name.asc()

    ).all()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([

        "Company",

        "Country",

        "Email"

    ])

    for buyer in buyers:

        writer.writerow([

            buyer.company_name,

            buyer.country,

            buyer.email

        ])

    memory_file = io.BytesIO()

    memory_file.write(

        output.getvalue().encode(

            "utf-8"

        )

    )

    memory_file.seek(0)

    output.close()

    return send_file(

        memory_file,

        mimetype="text/csv",

        as_attachment=True,

        download_name="buyers.csv"

    )

# ==========================================
# IMPORT BUYERS FROM CSV
# ==========================================

@buyers_bp.route("/api/buyers/import", methods=["POST"])
def import_buyers():

    if "file" not in request.files:

        return jsonify({

            "success": False,

            "message": "No file uploaded."

        }), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify({

            "success": False,

            "message": "No file selected."

        }), 400

    try:

        stream = io.StringIO(

            file.stream.read().decode(

                "utf-8"

            )

        )

        reader = csv.DictReader(stream)

        imported = 0
        skipped = 0

        for row in reader:

            company = (

                row.get(

                    "Company",

                    ""

                ).strip()

            )

            country = (

                row.get(

                    "Country",

                    ""

                ).strip()

            )

            email = (

                row.get(

                    "Email",

                    ""

                ).strip().lower()

            )

            if not company or not email:

                skipped += 1
                continue

            existing = Buyer.query.filter_by(

                email=email

            ).first()

            if existing:

                skipped += 1
                continue

            buyer = Buyer(

                company_name=company,

                country=country,

                email=email

            )

            db.session.add(

                buyer

            )

            imported += 1

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Import completed successfully.",

            "imported": imported,

            "skipped": skipped

        })

    except IntegrityError:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": "Duplicate email found in CSV."

        }), 400

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500