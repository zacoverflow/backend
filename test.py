from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Access Google Maps API key from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

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

    # Extract route information
    route_info = directions_data['routes'][0]
    overview_polyline = route_info['overview_polyline']['points']
    tolls = any(leg['hasTolls'] for leg in route_info['legs'])
    total_distance = sum(leg['distance']['value'] for leg in route_info['legs'])  # in meters
    total_duration = sum(leg['duration']['value'] for leg in route_info['legs'])  # in seconds

    return jsonify({
        'overview_polyline': overview_polyline,
        'total_distance_m': total_distance,
        'total_duration_s': total_duration,
        'tolls': tolls,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
