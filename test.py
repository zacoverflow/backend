from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Replace with your actual Google Maps API key
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

def geocode_address(address):
    """Geocode an address using the Google Maps API."""
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return {'latitude': location['lat'], 'longitude': location['lng']}
    else:
        return None

@app.route('/get-coordinates', methods=['GET'])
def get_coordinates():
    origin_address = request.args.get('origin')
    destination_address = request.args.get('destination')

    if not origin_address or not destination_address:
        return jsonify({'error': 'Both origin and destination addresses are required'}), 400

    # Geocode the origin and destination
    origin_coords = geocode_address(origin_address)
    destination_coords = geocode_address(destination_address)

    if origin_coords and destination_coords:
        return jsonify({'origin': origin_coords, 'destination': destination_coords})
    else:
        return jsonify({'error': 'Failed to geocode one or both addresses'}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
