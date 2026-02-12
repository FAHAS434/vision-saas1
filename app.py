from flask import Flask, render_template
from models import db
from dashboard.routes import dashboard_bp
from api import api_bp
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)

# ✅ AJOUTE ÇA
@app.route("/")
def home():
    return render_template("landing.html")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
