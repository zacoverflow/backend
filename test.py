from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

# Access Google Maps API key from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
TOLL_CALCULATOR_URL = "https://api.transport.nsw.gov.au/v2/roads/toll_calc/match"
NSW_TOLL_API_KEY = os.environ.get("NSW_TOLL_API_Key")

def get_toll_cost(polyline):
    """Calculate toll costs for a route using the toll calculator API."""
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': NSW_TOLL_API_KEY
    }
    data = {
        "accuracy": 10,
        "departureTime": datetime.now().astimezone().isoformat(),
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
    
    # Debug output to check response details
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
    
    # Parse response if successful
    if response.status_code == 200:
        toll_data = response.json()
        if "match" in toll_data and "tollsCharged" in toll_data["match"]:
            tolls = toll_data["match"]["tollsCharged"]
            total_toll_cost = sum(charge["chargeInCents"] for toll in tolls for charge in toll["charges"]) / 100  # Convert cents to dollars
            return {"toll_cost": total_toll_cost, "currency": "AUD"}
        else:
            return {"toll_cost": 0, "currency": "AUD"}
    else:
        return {"error": response.json()}

def get_directions(origin, destination):
    """Get driving directions from origin to destination using Google Maps API."""
    url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': origin,
        'destination': destination,
        'mode': 'driving',
        'alternatives': 'false',  # To get only the fastest route
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

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

    # Extract detailed points from each step
    route_points = []
    for leg in directions_data['routes'][0]['legs']:
        for step in leg['steps']:
            step_polyline = step['polyline']['points']
            route_points.append(step_polyline)

    overview_polyline = directions_data['routes'][0]['overview_polyline']['points']
    total_distance = sum(leg['distance']['value'] for leg in directions_data['routes'][0]['legs'])  # in meters
    total_duration = sum(leg['duration']['value'] for leg in directions_data['routes'][0]['legs'])  # in seconds
    tolls = get_toll_cost(overview_polyline)
    
    return jsonify({
        'overview_polyline': overview_polyline,
        'detailed_route_points': route_points,
        'total_distance_m': total_distance,
        'total_duration_s': total_duration,
        'fare': tolls
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
