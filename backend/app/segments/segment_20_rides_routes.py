from flask import Blueprint, request, jsonify

ride_bp = Blueprint("ride_bp", __name__, url_prefix="/api/ride")


@ride_bp.post("/request")
def request_ride():
    data = request.get_json(silent=True) or {}
    pickup = (data.get("pickup") or "").strip()
    dropoff = (data.get("dropoff") or "").strip()
    vehicle = (data.get("vehicle") or "car").strip()

    if not pickup or not dropoff:
        return jsonify({"message": "Pickup and dropoff are required"}), 400

    # For now: return a quick simulated ride request.
    # Later: connect to your dispatch/AI segments.
    return jsonify({
        "message": "Ride requested",
        "ride": {
            "id": "ride_demo_001",
            "pickup": pickup,
            "dropoff": dropoff,
            "vehicle": vehicle,
            "status": "searching_driver"
        }
    }), 200