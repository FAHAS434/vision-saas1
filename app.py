from flask import Flask
from models import db
from dashboard import dashboard_bp
from api import api_bp
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)

with app.app_context():
    db.create_all()  # Créer la DB si elle n'existe pas

if __name__ == "__main__":
    app.run(debug=True)
