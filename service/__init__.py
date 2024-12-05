from flask import Flask, jsonify
from flask_cors import CORS
from service import models
import logging
import os

# Create Flask application
app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy database URI from environment variable
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:Ma0919213023@localhost:5432/postgres"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
models.init_db(app)

from service import (
    routes,
)  # Assuming routes.py has been created with necessary endpoints

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask.app")


@app.route("/")
def index():
    return jsonify(message="Welcome to the Product Service API!"), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
