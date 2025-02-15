import requests
import os

MAPBOX_API_KEY = os.getenv('MAPBOX_API_KEY')

def get_lat_lon_from_address(address, city=None, state=None, country="USA"):
    """
    Brings the most accurate lat/lon data of the address from Mapbox.
    - If there is city and state information, it gets more accurate results by adding them.
    - It selects the most accurate one from the incoming data.
    """

    # **Create address details**
    # query = f"{address}"
    # if city:
    #     query += f", {city}"
    # if state:
    #     query += f", {state}"
    # query += f", {country}"

    # url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    # params = {
    #     "access_token": MAPBOX_API_KEY,
    #     "limit": 3,  # To get more alternatives
    #     "types": "address,poi,place"  # Just for important places
    # }

    # response = requests.get(url, params=params)
    # data = response.json()

    # if "features" not in data or not data["features"]:
    #     print(f"⚠️ No valid location found for: {query}")
    #     return None, None

    # best_result = data["features"][0]  # First result and probably the best one
    # lat = best_result["geometry"]["coordinates"][1]
    # lon = best_result["geometry"]["coordinates"][0]

    # print(f"✅ Address found: {query} → {lat}, {lon}")
    # return lat, lon
