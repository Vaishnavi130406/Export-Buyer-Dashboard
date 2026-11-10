from flask import Blueprint, jsonify
from datetime import datetime

from models import db
from models.buyer import Buyer
from models.email_history import EmailHistory


dashboard_bp = Blueprint("dashboard", __name__)


# ==============================
# Dashboard Statistics API
# ==============================

@dashboard_bp.route("/api/dashboard", methods=["GET"])
def dashboard_stats():

    total_buyers = Buyer.query.count()


    emails_sent = EmailHistory.query.filter_by(
        status="Sent"
    ).count()


    today = datetime.today().date()


    today_emails = EmailHistory.query.filter(
        db.func.date(EmailHistory.sent_at) == today
    ).count()


    pending_emails = EmailHistory.query.filter_by(
        status="Pending"
    ).count()


    return jsonify({

        "total_buyers": total_buyers,

        "emails_sent": emails_sent,

        "today_searches": today_emails,

        "pending_emails": pending_emails

    })



# ==============================
# Buyers By Country API
# ==============================

@dashboard_bp.route("/api/dashboard/countries", methods=["GET"])
def buyers_by_country():


    country_data = (
        db.session.query(
            Buyer.country,
            db.func.count(Buyer.id)
        )
        .group_by(Buyer.country)
        .all()
    )


    result = []


    for country, count in country_data:

        result.append({

            "country": country,

            "buyers": count

        })


    return jsonify(result)
# ==============================
# Email Activity API
# ==============================

@dashboard_bp.route("/api/dashboard/emails", methods=["GET"])
def email_activity():

    email_data = (
        db.session.query(
            db.func.date(EmailHistory.sent_at),
            db.func.count(EmailHistory.id)
        )
        .group_by(
            db.func.date(EmailHistory.sent_at)
        )
        .order_by(
            db.func.date(EmailHistory.sent_at)
        )
        .all()
    )


    result = []


    for date, count in email_data:

        result.append({

            "date": str(date),

            "emails": count

        })


    return jsonify(result)
# ==============================
# Monthly Email Activity API
# ==============================

@dashboard_bp.route("/api/dashboard/monthly", methods=["GET"])
def monthly_email_activity():


    monthly_data = (
        db.session.query(
            db.func.to_char(
                EmailHistory.sent_at,
                "Month"
            ),
            db.func.count(
                EmailHistory.id
            )
        )
        .group_by(
            db.func.to_char(
                EmailHistory.sent_at,
                "Month"
            )
        )
        .order_by(
            db.func.min(
                EmailHistory.sent_at
            )
        )
        .all()
    )


    result = []


    for month, count in monthly_data:

        result.append({

            "month": month.strip(),

            "emails": count

        })


    return jsonify(result)