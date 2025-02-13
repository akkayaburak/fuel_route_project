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
            return JsonResponse({
                "route": route_data,
                "optimal_fuel_stations": [],  # No fuel stops needed
                "total_fuel_cost": total_cost
            })
        
        # Fetch available fuel stations from the database
        fuel_stations = list(FuelStation.objects.all().values())
        if not fuel_stations:
            return JsonResponse({"error": "No fuel stations available"}, status=500)
        
        # Compute the optimal fuel stations along the route
        optimal_stations = get_optimal_fuel_stations(route_data, fuel_stations, max_range)
        
        # Compute the total fuel cost
        total_cost = calculate_fuel_cost(route_data, 3.50) 
        
        return JsonResponse({
            "route": route_data,
            "optimal_fuel_stations": optimal_stations,
            "total_fuel_cost": total_cost
        })
    else:
        return JsonResponse({"error": "Error fetching route data from ORS"}, status=500)


def get_optimal_fuel_stations(route_data, fuel_stations, max_range=500):
    """
    Determines the optimal fuel stations along the route. The vehicle has a maximum range of `max_range` miles,
    so stops are determined based on:
      - Proximity to the route (within 5 miles)
      - The best fuel price at each necessary stop
      - Ensuring stops are made before running out of fuel
    """
    optimal_stations = []
    route_geometry = route_data.get('routes', [{}])[0].get('geometry')
    
    if not route_geometry:
        print("Error: Route geometry not found!")
        return []

    decoded_route = polyline.decode(route_geometry)  # Decode polyline to get (lat, lon) points
    total_distance_miles = route_data.get('routes', [{}])[0].get('summary', {}).get('distance', 0) / 1609.34  
    if total_distance_miles == 0:
        print("Error: Route distance not found!")
        return []

    current_mileage = 0  # Track the vehicle's mileage along the route

    while current_mileage < total_distance_miles:
        next_stop_mileage = min(current_mileage + max_range, total_distance_miles)
        candidate_stations = []

        for station in fuel_stations:
            station_lat = station.get('lat')
            station_lon = station.get('lon')
            station_price = station.get('price')

            if station_lat is None or station_lon is None or station_price is None:
                continue  # Skip stations with missing data

            for i in range(int(current_mileage), int(next_stop_mileage), 10):  # Check every 10 miles
                if i < len(decoded_route):
                    route_point = decoded_route[i]
                    station_distance = haversine(route_point[0], route_point[1], station_lat, station_lon)
                    
                    if station_distance is not None and station_distance <= 5:  # Check proximity
                        candidate_stations.append(station)

        if candidate_stations:
            best_station = min(candidate_stations, key=lambda x: x['price'])  # Pick the cheapest
            optimal_stations.append(best_station)
            current_mileage = next_stop_mileage  # Move to the next range
        else:
            current_mileage += 50  # Move forward and retry

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