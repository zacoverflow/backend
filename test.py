from flask import Flask, request, jsonify
import os
import asyncio
import aiohttp
from datetime import datetime

app = Flask(__name__)

# Access Google Maps API key from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
TOLL_CALCULATOR_URL = "https://api.transport.nsw.gov.au/v2/roads/toll_calc/match"
NSW_TOLL_API_KEY = os.environ.get("NSW_TOLL_API_KEY")

@app.route('/get-fare', methods=['GET'])
async def get_toll_cost(polyline):
    """Calculate toll costs for a route using the toll calculator API."""
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': 'apikey eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBQmFvM1ZOMFdxUmhRLTRxdDcyR21BcWUzLVZac2V3WUZGYzdGc2NNQzdVIiwiaWF0IjoxNzMxMTUwMzA5fQ.RwVmJTADbu5iNG_M7xHvurY7qd9dTiFx-p6nMUWiLDI'
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

    async with aiohttp.ClientSession() as session:
        async with session.post(TOLL_CALCULATOR_URL, json=data, headers=headers) as response:
            toll_data = await response.json()
            if response.status == 200 and "match" in toll_data and "tollsCharged" in toll_data["match"]:
                tolls = toll_data["match"]["tollsCharged"]
                total_toll_cost = sum(charge["chargeInCents"] for toll in tolls for charge in toll["charges"]) / 100  # Convert cents to dollars
                return {"toll_cost": total_toll_cost, "currency": "AUD"}
            else:
                return {"toll_cost": 0, "currency": "AUD"}

async def get_directions(origin, destination):
    """Get driving directions from origin to destination using Google Maps API."""
    url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': origin,
        'destination': destination,
        'mode': 'driving',
        'alternatives': 'false',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()

@app.route('/get-route', methods=['GET'])
async def get_route():
    origin_address = request.args.get('origin')
    destination_address = request.args.get('destination')

    if not origin_address or not destination_address:
        return jsonify({'error': 'Both origin and destination addresses are required'}), 400

    # Run get_directions to retrieve overview_polyline first
    directions_data = await get_directions(origin_address, destination_address)
    if directions_data['status'] != 'OK':
        return jsonify({'error': 'Failed to retrieve directions'}), 400

    # Extract overview_polyline for get_toll_cost
    overview_polyline = directions_data['routes'][0]['overview_polyline']['points']

    # Extract detailed points from each step
    route_points = [
        step['polyline']['points']
        for leg in directions_data['routes'][0]['legs']
        for step in leg['steps']
    ]

    total_distance = sum(leg['distance']['value'] for leg in directions_data['routes'][0]['legs'])  # in meters
    total_duration = sum(leg['duration']['value'] for leg in directions_data['routes'][0]['legs'])  # in seconds

    return jsonify({
        'overview_polyline': overview_polyline,
        'detailed_route_points': route_points,
        'total_distance_m': total_distance,
        'total_duration_s': total_duration,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

