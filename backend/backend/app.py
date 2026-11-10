from flask import Flask
from flask_cors import CORS
from config import Config

from models import db

# Import Models
from models.buyer import Buyer
from models.email_history import EmailHistory

# Import Routes
from routes.buyers import buyers_bp
from routes.search import search_bp
from routes.dashboard import dashboard_bp
from routes.email import email_bp
from routes.history import history_bp
from routes.scraper import scraper_bp

app = Flask(__name__)

app.config.from_object(Config)

CORS(app)

db.init_app(app)

# Register Blueprints
app.register_blueprint(buyers_bp)
app.register_blueprint(search_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(email_bp)
app.register_blueprint(history_bp)
app.register_blueprint(
    scraper_bp
)


@app.route("/")
def home():
    return "Export Dashboard API Running"


if __name__ == "__main__":
    app.run(debug=True)