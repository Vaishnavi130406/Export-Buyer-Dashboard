from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db

# ==============================
# Import Models
# ==============================

from models.buyer import Buyer
from models.email_history import EmailHistory

# ==============================
# Import Blueprints
# ==============================

from routes.buyers import buyers_bp
from routes.dashboard import dashboard_bp
from routes.buyer_search import buyer_search_bp
from routes.email import email_bp
from routes.history import history_bp
from routes.scraper import scraper_bp
from routes.crm import crm_bp

# ==============================
# Create Flask App
# ==============================

app = Flask(__name__)

app.config.from_object(Config)

# ==============================
# Enable CORS
# ==============================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]
        }
    },
    supports_credentials=True
)

# ==============================
# Initialize Database
# ==============================

db.init_app(app)

# ==============================
# Register Blueprints
# ==============================

app.register_blueprint(buyers_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(buyer_search_bp)
app.register_blueprint(email_bp)
app.register_blueprint(history_bp)
app.register_blueprint(scraper_bp)
app.register_blueprint(crm_bp)

# ==============================
# Root Endpoint
# ==============================

@app.route("/")
def home():

    return jsonify({

        "success": True,

        "message": "Export Dashboard API Running Successfully"

    })


# ==============================
# Health Check
# ==============================

@app.route("/health")
def health():

    return jsonify({

        "status": "OK",

        "database": "Connected"

    })


# ==============================
# Global Error Handler
# ==============================

@app.errorhandler(Exception)
def handle_exception(error):

    print("\n========== ERROR ==========")
    print(error)
    print("===========================\n")

    return jsonify({

        "success": False,

        "message": str(error)

    }), 500


# ==============================
# Create Database Tables
# ==============================

with app.app_context():

    db.create_all()


# ==============================
# Run Server
# ==============================

if __name__ == "__main__":

    print("\n========================================")
    print(" Export Buyer Dashboard Backend Started ")
    print("========================================")
    print("API      : http://127.0.0.1:5000")
    print("Health   : http://127.0.0.1:5000/health")
    print("========================================\n")

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True,

        threaded=True

    )