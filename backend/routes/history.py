from flask import Blueprint, jsonify
from models.email_history import EmailHistory

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/email-history", methods=["GET"])
def email_history():

    history = EmailHistory.query.order_by(
        EmailHistory.sent_at.desc()
    ).all()

    return jsonify([

        item.to_dict()

        for item in history

    ])