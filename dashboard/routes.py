from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app as app
from models import db, User, ApiUsage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import secrets
import stripe

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ===== REGISTER =====
@dashboard_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("User already exists", "error")
            return redirect(url_for("dashboard.register"))

        user = User(
            email=email,
            password=generate_password_hash(password),
            api_key=secrets.token_hex(16)
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("dashboard.login"))

    return render_template("landing.html")  # peut aussi créer register.html

# ===== LOGIN =====
@dashboard_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard.profile"))

        flash("Invalid login", "error")
        return redirect(url_for("dashboard.login"))

    return render_template("landing.html")  # login page

# ===== LOGOUT =====
@dashboard_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("dashboard.login"))

# ===== PROFILE / DASHBOARD =====
@dashboard_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("dashboard.login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("dashboard.login"))

    today = date.today()
    usages = ApiUsage.query.filter_by(api_key=user.api_key, date=today).all()
    total_calls = sum(u.count for u in usages)

    limit_map = {"free": 10, "pro": 1000}
    limit = limit_map.get(user.plan, 10)
    percent = min(int((total_calls / limit) * 100), 100)

    api_expired = datetime.utcnow() > user.api_key_expires

    return render_template(
        "profile.html",
        email=user.email,
        api_key=user.api_key,
        plan=user.plan,
        usages=usages,
        total_calls=total_calls,
        percent=percent,
        limit=limit,
        api_expired=api_expired
    )

# ===== Stripe Upgrade =====
@dashboard_bp.route("/subscribe", methods=["POST"])
def subscribe():
    if "user_id" not in session:
        return redirect(url_for("dashboard.login"))

    user = User.query.get(session["user_id"])
    stripe.api_key = app.config["STRIPE_SECRET_KEY"]

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'VisionAPI Pro Plan'},
                'unit_amount': 1900,
                'recurring': {'interval': 'month'}
            },
            'quantity': 1
        }],
        mode='subscription',
        success_url=url_for('dashboard.upgrade_success', _external=True),
        cancel_url=url_for('dashboard.profile', _external=True),
        customer_email=user.email
    )
    return redirect(checkout_session.url)

@dashboard_bp.route("/upgrade_success")
def upgrade_success():
    if "user_id" not in session:
        return redirect(url_for("dashboard.login"))

    user = User.query.get(session["user_id"])
    user.plan = "pro"
    db.session.commit()
    flash("Pro Plan activated! 💎", "success")
    return redirect(url_for("dashboard.profile"))
