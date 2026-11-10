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