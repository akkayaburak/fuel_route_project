import requests
import os

MAPBOX_API_KEY = os.getenv('MAPBOX_API_KEY')

def get_lat_lon_from_address(address):
    # url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    # params = {
    #     "access_token": MAPBOX_API_KEY,
    #     "limit": 1
    # }
    # response = requests.get(url, params=params)
    # data = response.json()

    # if data['features']:
    #     lat = data['features'][0]['geometry']['coordinates'][1]
    #     lon = data['features'][0]['geometry']['coordinates'][0]
    #     return lat, lon
    return None, None
