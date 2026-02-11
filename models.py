from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import secrets

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    plan = db.Column(db.String(20), default="free")
    api_key_created = db.Column(db.DateTime, default=datetime.utcnow)
    api_key_expires = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

class ApiUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(64), nullable=False)
    endpoint = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, default=date.today)
