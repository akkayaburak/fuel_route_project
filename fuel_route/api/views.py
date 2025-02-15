from django.http import JsonResponse
from fuel_route.models import FuelStation
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
import json

# Retrieve API key for OpenRouteService (ORS) from environment variables
ORS_API_KEY = os.getenv('ORS_API_KEY')

@csrf_exempt
def calculate_route(request):
    """
    API endpoint that calculates an optimal fuel-up route between a start and end location in the USA.
    The function determines the optimal fuel stations along the route based on:
      - The vehicle's maximum range (500 miles)
      - Fuel station proximity to the route (within 5 miles)
      - The lowest fuel price at each required stop
    
    Returns:
      - The full route from OpenRouteService (ORS)
      - The list of optimal fuel stations along the route
      - The total fuel cost for the trip
    """
    
    # Parse JSON request body
    data = json.loads(request.body)
    start_lat = data.get("start_lat")
    start_lon = data.get("start_lon")
    end_lat = data.get("end_lat")
    end_lon = data.get("end_lon")
    
    # Validate input coordinates
    if not all([start_lat, start_lon, end_lat, end_lon]):
        return JsonResponse({"error": "Invalid input: Missing coordinates"}, status=400)
    
    # Call OpenRouteService API to retrieve route details
    ors_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    payload = {"coordinates": [[start_lon, start_lat], [end_lon, end_lat]]}
    headers = {"Authorization": ORS_API_KEY}
    response = requests.post(ors_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        route_data = response.json()
        
        # Convert total route distance from meters to miles
        total_distance_meters = route_data['routes'][0]['segments'][0]['distance']
        total_distance_miles = total_distance_meters / 1609.34  # 1 mile = 1609.34 meters
        max_range = 500  # Maximum vehicle range in miles
        
        # If the total route distance is within one tank (500 miles), no fuel stops needed
        if total_distance_miles <= max_range:
            total_cost = calculate_fuel_cost(route_data, 3.50)  # Assuming $3.50 per gallon
            return format_geojson_response(route_data, [], total_cost)
        
        # Fetch available fuel stations from the database
        fuel_stations = list(FuelStation.objects.all().values())
        if not fuel_stations:
            return JsonResponse({"error": "No fuel stations available"}, status=500)
        
        # Compute the optimal fuel stations along the route
        optimal_stations = get_optimal_fuel_stations(route_data, fuel_stations, max_range)
        
        # Compute the total fuel cost
        total_cost = calculate_fuel_cost(route_data, 3.50) 
        
        return format_geojson_response(route_data, optimal_stations, total_cost)
    else:
        return JsonResponse({"error": "Error fetching route data from ORS"}, status=500)


def format_geojson_response(route_data, optimal_stations, total_cost):
    """
    Converts the route data and fuel stations into a GeoJSON response for easy map rendering.
    
    Parameters:
    - route_data: The route JSON from ORS
    - optimal_stations: The list of optimal fuel stations
    - total_cost: The total fuel cost for the journey
    
    Returns:
    - A JsonResponse with GeoJSON formatted route and stations
    """

    # Convert route geometry to GeoJSON format
    route_geometry = polyline.decode(route_data['routes'][0]['geometry'])
    geojson_route = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in route_geometry]
        },
        "properties": {
            "total_fuel_cost": total_cost
        }
    }

    # Convert fuel stations to GeoJSON format (with safety checks)
    geojson_stations = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [station["lon"], station["lat"]]
            },
            "properties": {
                "name": station.get("name", "Unknown"),
                "price": station.get("price", "Unknown"),
                "address": station.get("address", "Unknown"),
                "city": station.get("city", "Unknown"),
                "state": station.get("state", "Unknown")
            }
        }
        for station in optimal_stations
    ]

    # Final GeoJSON response
    geojson_response = {
        "type": "FeatureCollection",
        "features": [geojson_route] + geojson_stations
    }

    return JsonResponse(geojson_response, safe=False)


def get_optimal_fuel_stations(route_data, fuel_stations, max_range=500, min_range=300):
    """
    Finds the most cost-effective fuel stations along a route.
    - Prioritizes the cheapest fuel stations within a given distance.
    - Scans through route waypoints to find fuel stations close to the route.
    - If no fuel station is found within 500 miles, it decreases the range to 300 miles.
    
    Parameters:
        route_data: (dict) Route information (from OpenRouteService or similar API)
        fuel_stations: (list) List of available fuel stations
        max_range: (int) Maximum fuel range before refueling (default: 500 miles)
        min_range: (int) Minimum distance between refueling stops (default: 300 miles)
        
    Returns:
        optimal_stations (list): The best fuel stations along the route
    """
    optimal_stations = []  # Stores the selected fuel stops
    
    # **1️⃣ Extract route geometry**
    route_geometry = route_data.get('routes', [{}])[0].get('geometry')
    if not route_geometry:
        print("❌ Error: Route geometry not found!")
        return []

    # **2️⃣ Decode the route and calculate total distance**
    decoded_route = polyline.decode(route_geometry)  # Get all waypoints in the route
    total_distance_miles = route_data.get('routes', [{}])[0].get('summary', {}).get('distance', 0) / 1609.34  
    if total_distance_miles == 0:
        print("❌ Error: Route distance not found!")
        return []

    current_mileage = 0  # Tracks the vehicle's current mileage
    previous_station = None  # Keeps track of the last fuel stop

    # **3️⃣ Extract the starting point**
    start_lat, start_lon = decoded_route[0]

    while current_mileage < total_distance_miles:
        # **4️⃣ Define the next stop range for refueling**
        next_stop_mileage = min(current_mileage + max_range, total_distance_miles)
        candidate_stations = []  # Stores fuel stations within the current range
        seen_stations = {}  # Keeps track of the cheapest station per location

        print(f"\n🚗 Checking fuel stations between {current_mileage}-{next_stop_mileage} miles")

        # **5️⃣ Iterate through all fuel stations**
        for station in fuel_stations:
            station_lat = station.get('lat')
            station_lon = station.get('lon')
            station_price = float(station.get('price', 0))

            # 🚨 **Conditions:**
            # - Skip stations with missing latitude/longitude
            # - Ignore stations too close to the starting point (<50 miles)
            if station_lat is None or station_lon is None or station_price is None:
                continue

            if haversine(start_lat, start_lon, station_lat, station_lon) < 50:
                continue

            station_key = (station_lat, station_lon)
            if station_key in seen_stations:
                # **Keep the cheapest station for each location**
                if station_price < seen_stations[station_key]['price']:
                    seen_stations[station_key] = station
            else:
                seen_stations[station_key] = station

        # **6️⃣ Check for stations near the route**
        for station in seen_stations.values():
            for i in range(int(current_mileage), int(next_stop_mileage), 10):  # Scan every 10 miles along the route
                if i < len(decoded_route):
                    route_point = decoded_route[i]
                    station_distance = haversine(route_point[0], route_point[1], station["lat"], station["lon"])

                    # **Add station if it's within 5 miles of the route**
                    if station_distance is not None and station_distance <= 5:
                        candidate_stations.append(station)

        # **7️⃣ Select the best fuel station**
        if candidate_stations:
            # ✅ **Pick the cheapest station**
            best_station = min(candidate_stations, key=lambda x: x['price'])

            # 🚨 **Skip station if it's too close to the previous stop**
            if previous_station:
                distance_between = haversine(previous_station['lat'], previous_station['lon'], best_station['lat'], best_station['lon'])
                if distance_between < min_range:
                    print(f"❌ Skipping {best_station['name']} (Too close to previous station)")
                    current_mileage += 100
                    continue

            print(f"✅ Fuel stop: {best_station['name']} at {best_station['lat']}, {best_station['lon']} - Price: ${best_station['price']}")
            optimal_stations.append(best_station)
            previous_station = best_station  # Update the last refueling station
            current_mileage = next_stop_mileage  # Continue from the refueling point

        else:
            # **If no station is found, reduce the distance and retry**
            print(f"⚠️ No suitable fuel station found in range {current_mileage}-{next_stop_mileage} miles")
            current_mileage += 100  # Increase mileage by 100 miles and retry

    return optimal_stations



def haversine(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate the great-circle distance between two points on Earth.
    Formula:
      a = sin²(Δφ/2) + cos(φ1) ⋅ cos(φ2) ⋅ sin²(Δλ/2)
      c = 2 ⋅ atan2(√a, √(1−a))
      d = R ⋅ c
    Where:
      - φ1, λ1: Latitude and Longitude of first point (in radians)
      - φ2, λ2: Latitude and Longitude of second point (in radians)
      - R = 3959 miles (Earth’s radius)
    """
    try:
        R = 3959  # Earth's radius in miles
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # Distance in miles
    except Exception as e:
        print(f"Error in haversine calculation: {e}")
        return None


def calculate_fuel_cost(route_data, fuel_price_per_gallon):
    """
    Calculates the total fuel cost for the trip.
    Formula:
      total_gallons = total_distance_miles / 10
      total_cost = total_gallons * fuel_price_per_gallon
    """
    total_distance = sum(segment['distance'] for segment in route_data['routes'][0]['segments'])
    total_fuel_needed = total_distance / 1609.34 / 10  # Convert meters to miles, then divide by MPG
    return total_fuel_needed * fuel_price_per_gallon