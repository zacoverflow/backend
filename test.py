from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Access API keys from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
TOLL_CALCULATOR_URL = "https://api.transport.nsw.gov.au/v2/roads/toll_calc/match"  # Replace with the actual endpoint

def get_directions(origin, destination):
    """Get driving directions from origin to destination using Google Maps API."""
    url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': origin,
        'destination': destination,
        'mode': 'driving',
        'alternatives': 'false',
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

def get_toll_cost(polyline):
    """Calculate toll costs for a route using the toll calculator API."""
    headers = {'Content-Type': 'application/json'}
    data = {
        "accuracy": 10,
        "departureTime": datetime.now().isoformat(),
        "includeSteps": False,
        "polyline": polyline,
        "vehicleClass": "A",
        "vehicleClassByMotorway": {
            "CCT": "A",
            "ED": "A",
            "LCT": "A",
            "M2": "A",
            "M4": "A",
            "M5": "A",
            "M7": "A",
            "SHB": "A",
            "SHT": "A"
        }   
    }

    response = requests.post(TOLL_CALCULATOR_URL, json=data, headers=headers)
    toll_data = response.json()

    # Extract toll information if available
    if toll_data and "match" in toll_data and "tollsCharged" in toll_data["match"]:
        tolls = toll_data["match"]["tollsCharged"]
        total_toll_cost = sum(charge["chargeInCents"] for toll in tolls for charge in toll["charges"]) / 100  # Convert cents to dollars
        return {"toll_cost": total_toll_cost, "currency": "AUD"}
    else:
        return {"toll_cost": 0, "currency": "AUD"}

@app.route('/get-route', methods=['GET'])
def get_route():
    origin_address = request.args.get('origin')
    destination_address = request.args.get('destination')

    if not origin_address or not destination_address:
        return jsonify({'error': 'Both origin and destination addresses are required'}), 400

    # Get directions data
    directions_data = get_directions(origin_address, destination_address)

    if directions_data['status'] != 'OK':
        return jsonify({'error': 'Failed to retrieve directions'}), 400

    # Extract route information
    overview_polyline = directions_data['routes'][0]['overview_polyline']['points']
    total_distance = sum(leg['distance']['value'] for leg in directions_data['routes'][0]['legs'])  # in meters
    total_duration = sum(leg['duration']['value'] for leg in directions_data['routes'][0]['legs'])  # in seconds

    # Get toll cost for the polyline route
    toll_info = get_toll_cost(overview_polyline)

    return jsonify({
        'overview_polyline': overview_polyline,
        'total_distance_m': total_distance,
        'total_duration_s': total_duration,
        'toll_cost': toll_info["toll_cost"],
        'currency': toll_info["currency"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

