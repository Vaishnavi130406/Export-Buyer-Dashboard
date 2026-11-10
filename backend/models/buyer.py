from datetime import datetime
from models import db
class Buyer(db.Model):
    __tablename__ = "buyers"

    id = db.Column(db.Integer, primary_key=True)

    # Buyer Information
    company_name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    email = db.Column(db.String(200))
    website = db.Column(db.String(500))
    source = db.Column(db.String(100))

    # CRM Fields
    lead_status = db.Column(
        db.String(50),
        default="Email Sent"
    )

    priority = db.Column(
        db.String(20),
        default="Medium"
    )

    assigned_to = db.Column(
        db.String(100),
        default="Sales Team"
    )

    notes = db.Column(
        db.Text,
        default=""
    )

    last_email_date = db.Column(
        db.DateTime,
        nullable=True
    )

    followup_date = db.Column(
        db.DateTime,
        nullable=True
    )

    next_followup = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "country": self.country,
            "email": self.email,
            "website": self.website,
            "source": self.source,

            "lead_status": self.lead_status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "notes": self.notes,

            "last_email_date": self.last_email_date.strftime("%Y-%m-%d")
            if self.last_email_date else None,

            "followup_date": self.followup_date.strftime("%Y-%m-%d")
            if self.followup_date else None,

            "next_followup": self.next_followup.strftime("%Y-%m-%d")
            if self.next_followup else None,

            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),

            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M")
        }