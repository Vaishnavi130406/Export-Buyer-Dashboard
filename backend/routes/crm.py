from flask import Blueprint, jsonify, request
from sqlalchemy import or_, asc, desc
from datetime import datetime, timedelta

from models import db
from models.buyer import Buyer

crm_bp = Blueprint("crm", __name__)


# ==========================================================
# Helper: Automatic Follow-up Detection
# ==========================================================

def update_followup_status():
    """
    Automatically marks leads as 'Follow-up Due'
    when the follow-up date has passed.
    """

    today = datetime.utcnow()

    buyers = Buyer.query.filter(
        Buyer.followup_date.isnot(None)
    ).all()

    updated = False

    for buyer in buyers:

        if (
            buyer.followup_date
            and buyer.followup_date <= today
            and buyer.lead_status
            not in [
                "Closed Lead",
                "Not Interested",
                "Follow-up Due",
            ]
        ):

            buyer.lead_status = "Follow-up Due"
            updated = True

    if updated:
        db.session.commit()


# ==========================================================
# CRM Dashboard Statistics
# ==========================================================

@crm_bp.route("/api/crm/stats", methods=["GET"])
def crm_stats():

    update_followup_status()

    buyers = Buyer.query.all()

    stats = {
        "total_buyers": len(buyers),

        "email_sent": Buyer.query.filter_by(
            lead_status="Email Sent"
        ).count(),

        "waiting_reply": Buyer.query.filter_by(
            lead_status="Waiting Reply"
        ).count(),

        "followup_due": Buyer.query.filter_by(
            lead_status="Follow-up Due"
        ).count(),

        "positive_reply": Buyer.query.filter_by(
            lead_status="Positive Reply"
        ).count(),

        "negotiation": Buyer.query.filter_by(
            lead_status="Negotiation"
        ).count(),

        "closed_lead": Buyer.query.filter_by(
            lead_status="Closed Lead"
        ).count(),

        "not_interested": Buyer.query.filter_by(
            lead_status="Not Interested"
        ).count()
    }

    return jsonify({

        "success": True,

        "stats": stats

    })


# ==========================================================
# GET ALL CRM LEADS
# Search + Filters + Sorting
# ==========================================================

@crm_bp.route("/api/crm/leads", methods=["GET"])
def crm_leads():

    update_followup_status()

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        "All"
    )

    priority = request.args.get(
        "priority",
        "All"
    )

    sort = request.args.get(
        "sort",
        "company_name"
    )

    order = request.args.get(
        "order",
        "asc"
    )

    query = Buyer.query

    # -------------------------------------
    # Search
    # -------------------------------------

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

    # -------------------------------------
    # Status Filter
    # -------------------------------------

    if status != "All":

        query = query.filter(

            Buyer.lead_status == status

        )

    # -------------------------------------
    # Priority Filter
    # -------------------------------------

    if priority != "All":

        query = query.filter(

            Buyer.priority == priority

        )

    # -------------------------------------
    # Sorting
    # -------------------------------------

    if hasattr(Buyer, sort):

        column = getattr(
            Buyer,
            sort
        )

        if order == "desc":

            query = query.order_by(
                desc(column)
            )

        else:

            query = query.order_by(
                asc(column)
            )

    buyers = query.all()

    return jsonify({

        "success": True,

        "count": len(buyers),

        "buyers": [

            buyer.to_dict()

            for buyer in buyers

        ]

    })
# ==========================================================
# UPDATE CRM LEAD
# ==========================================================

@crm_bp.route("/api/crm/update/<int:id>", methods=["PUT"])
def update_crm_lead(id):

    buyer = Buyer.query.get_or_404(id)

    data = request.get_json()

    buyer.lead_status = data.get(
        "lead_status",
        buyer.lead_status
    )

    buyer.priority = data.get(
        "priority",
        buyer.priority
    )

    buyer.assigned_to = data.get(
        "assigned_to",
        buyer.assigned_to
    )

    buyer.notes = data.get(
        "notes",
        buyer.notes
    )

    followup = data.get("followup_date")

    if followup:

        try:

            buyer.followup_date = datetime.strptime(
                followup,
                "%Y-%m-%d"
            )

        except Exception:

            return jsonify({

                "success": False,

                "message": "Invalid follow-up date format. Use YYYY-MM-DD."

            }), 400

    buyer.updated_at = datetime.utcnow()

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "message": "Lead updated successfully.",

            "buyer": buyer.to_dict()

        })

    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500