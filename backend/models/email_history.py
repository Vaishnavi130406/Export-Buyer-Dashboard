from models import db


class EmailHistory(db.Model):
    __tablename__ = "email_history"

    id = db.Column(db.Integer, primary_key=True)

    buyer_email = db.Column(db.String(150), nullable=False)

    subject = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), nullable=False)

    sent_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "id": self.id,
            "buyer_email": self.buyer_email,
            "subject": self.subject,
            "status": self.status,
            "sent_at": str(self.sent_at)
        }