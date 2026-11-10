from flask import Blueprint, request, jsonify
from email.message import EmailMessage
from dotenv import load_dotenv

from models import db
from models.buyer import Buyer
from models.email_history import EmailHistory

import os
import json
import smtplib

load_dotenv()

email_bp = Blueprint("email", __name__)


# ==========================================================
# SEND SINGLE EMAIL
# ==========================================================

@email_bp.route("/api/send-email", methods=["POST"])
def send_email():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received."
            }), 400

        receiver = data.get("email")
        subject = data.get("subject")
        message = data.get("message")

        if not receiver:
            return jsonify({
                "success": False,
                "error": "Receiver email is required."
            }), 400

        sender_email = os.getenv("SMTP_EMAIL")
        password = os.getenv("SMTP_PASSWORD")

        if not sender_email or not password:
            return jsonify({
                "success": False,
                "error": "SMTP credentials are missing in .env"
            }), 500

        msg = EmailMessage()

        msg["From"] = sender_email
        msg["To"] = receiver
        msg["Subject"] = subject

        msg.set_content(message)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            server.starttls()

            server.login(
                sender_email,
                password
            )

            server.send_message(msg)

        history = EmailHistory(
            buyer_email=receiver,
            subject=subject,
            status="Sent"
        )

        db.session.add(history)
        db.session.commit()

        return jsonify({

            "success": True,
            "message": "Email sent successfully."

        })

    except Exception as e:

        db.session.rollback()

        history = EmailHistory(
            buyer_email=receiver if 'receiver' in locals() else "",
            subject=subject if 'subject' in locals() else "",
            status="Failed"
        )

        db.session.add(history)
        db.session.commit()

        return jsonify({

            "success": False,
            "error": str(e)

        }), 500


# ==========================================================
# SEND EMAIL CAMPAIGN
# ==========================================================

@email_bp.route("/api/email/send-campaign", methods=["POST"])
def send_campaign():

    try:

        subject = request.form.get("subject", "").strip()

        message = request.form.get("message", "").strip()

        buyer_ids = json.loads(

            request.form.get(

                "buyer_ids",

                "[]"

            )

        )

        attachment = request.files.get("attachment")

        if not subject:

            return jsonify({

                "success": False,

                "error": "Subject is required."

            }), 400

        if not message:

            return jsonify({

                "success": False,

                "error": "Message is required."

            }), 400

        if len(buyer_ids) == 0:

            return jsonify({

                "success": False,

                "error": "No buyers selected."

            }), 400

        sender_email = os.getenv("SMTP_EMAIL")

        password = os.getenv("SMTP_PASSWORD")

        if not sender_email or not password:

            return jsonify({

                "success": False,

                "error": "SMTP credentials not configured."

            }), 500

        buyers = Buyer.query.filter(

            Buyer.id.in_(buyer_ids)

        ).all()

        sent = 0
        failed = 0
        for buyer in buyers:

            try:

                if not buyer.email:

                    failed += 1

                    history = EmailHistory(
                        buyer_email="",
                        subject=subject,
                        status="Failed"
                    )

                    db.session.add(history)
                    db.session.commit()

                    continue

                msg = EmailMessage()

                msg["From"] = sender_email
                msg["To"] = buyer.email
                msg["Subject"] = subject

                msg.set_content(message)

                # ===========================================
                # Attach PDF if uploaded
                # ===========================================

                if attachment:

                    attachment.stream.seek(0)

                    pdf_data = attachment.read()

                    msg.add_attachment(

                        pdf_data,

                        maintype="application",

                        subtype="pdf",

                        filename=attachment.filename

                    )

                # ===========================================
                # Send Email
                # ===========================================

                with smtplib.SMTP(

                    "smtp.gmail.com",

                    587

                ) as server:

                    server.starttls()

                    server.login(

                        sender_email,

                        password

                    )

                    server.send_message(msg)

                sent += 1

                history = EmailHistory(

                    buyer_email=buyer.email,

                    subject=subject,

                    status="Sent"

                )

                db.session.add(history)

                db.session.commit()

            except Exception as err:

                db.session.rollback()

                failed += 1

                history = EmailHistory(

                    buyer_email=buyer.email,

                    subject=subject,

                    status="Failed"

                )

                db.session.add(history)

                db.session.commit()

                print(

                    f"Failed to send email to {buyer.email}:",

                    err

                )
        return jsonify({

            "success": True,

            "message": "Email campaign completed successfully.",

            "recipients": len(buyers),

            "sent": sent,

            "failed": failed

        })

    except Exception as e:

        db.session.rollback()

        print("\n========== EMAIL CAMPAIGN ERROR ==========")
        print(str(e))
        print("==========================================\n")

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500