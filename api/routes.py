from flask import Blueprint, request, jsonify
from models import db, User, ApiUsage
from datetime import datetime, date

api_bp = Blueprint("api", __name__, url_prefix="/api")

PLANS = {
    "free": {"/slide": 10, "/rotate": 10, "/shapes": 10, "/icons": 10},
    "pro": {"/slide": 1000, "/rotate": 1000, "/shapes": 1000, "/icons": 1000}
}

def check_api_key(api_key):
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return None, jsonify({"error": "API key invalide"}), 401
    if user.api_key_expires and datetime.utcnow() > user.api_key_expires:
        return None, jsonify({"error": "API key expirée"}), 403
    return user, None, None

def check_quota(user, endpoint):
    limit = PLANS.get(user.plan, {}).get(endpoint, 0)
    today = date.today()

    usage = ApiUsage.query.filter_by(api_key=user.api_key, endpoint=endpoint, date=today).first()
    if not usage:
        usage = ApiUsage(api_key=user.api_key, endpoint=endpoint, count=1, date=today)
        db.session.add(usage)
        db.session.commit()
        return True

    if usage.count >= limit:
        return False

    usage.count += 1
    db.session.commit()
    return True

def create_endpoint(endpoint_name, example_response):
    @api_bp.route(f"/{endpoint_name}", methods=["POST"])
    def endpoint():
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return jsonify({"error": "API key manquante"}), 401

        user, err_resp, err_code = check_api_key(api_key)
        if err_resp:
            return err_resp, err_code

        if not check_quota(user, f"/{endpoint_name}"):
            return jsonify({"error": "Quota dépassé", "plan": user.plan}), 429

        resp = {"success": True, "plan": user.plan}
        resp.update(example_response)
        return jsonify(resp)
    return endpoint

create_endpoint("slide", {"x": 150, "message": "Slide exécuté"})
create_endpoint("rotate", {"angle": 120, "message": "Rotation exécutée"})
create_endpoint("shapes", {"points": [[10,10],[50,50]], "message": "Shapes détectées"})
create_endpoint("icons", {"points": [[5,5],[20,20]], "message": "Icons matching"})
