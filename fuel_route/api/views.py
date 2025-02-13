from django.http import JsonResponse
from fuel_route.models import FuelStation
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
import json

ORS_API_KEY = os.getenv('ORS_API_KEY')

@csrf_exempt
def calculate_route(request):
    data = json.loads(request.body)
    start_lat = data.get("start_lat")
    start_lon = data.get("start_lon")
    end_lat = data.get("end_lat")
    end_lon = data.get("end_lon")
    
    if not all([start_lat, start_lon, end_lat, end_lon]):
        return JsonResponse({"error": "Invalid input: Missing coordinates"}, status=400)
    
    # OpenRouteService API çağrısı
    ors_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    payload = {
        "coordinates": [
            [start_lon, start_lat],
            [end_lon, end_lat]
        ]
    }
    headers = {"Authorization": ORS_API_KEY}
    response = requests.post(ors_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        route_data = response.json()
        
        # Yolculuk mesafesini hesapla (metre cinsinden)
        total_distance_meters = route_data['routes'][0]['segments'][0]['distance']
        total_distance_miles = total_distance_meters / 1609.34  # Metreyi mile çevir
        
        # 500 mil menzil
        max_range = 500
        
        # Eğer rota mesafesi 500 milin altındaysa, yakıt alımına gerek yok
        if total_distance_miles <= max_range:
            total_cost = calculate_fuel_cost(route_data, 3.50) 
            return JsonResponse({
                "route": route_data,
                "optimal_fuel_stations": [],  # Yakıt istasyonu yok
                "total_fuel_cost": total_cost
            })
        
        # Yakıt istasyonlarını listele
        fuel_stations = list(FuelStation.objects.all().values())
        if not fuel_stations:
            return JsonResponse({"error": "No fuel stations available"}, status=500)
        
        # Optimum yakıt istasyonlarını al
        optimal_stations = get_optimal_fuel_stations(route_data, fuel_stations, max_range)
        
        # Toplam maliyeti hesapla (3.50 USD/gallon)
        total_cost = calculate_fuel_cost(route_data, 3.50) 
        
        # Sonuçları döndür
        return JsonResponse({
            "route": route_data,
            "optimal_fuel_stations": optimal_stations,
            "total_fuel_cost": total_cost
        })
    else:
        return JsonResponse({"error": "Error fetching route data from ORS"}, status=500)


def get_optimal_fuel_stations(route_data, fuel_stations, max_range=500):
    optimal_stations = []
    route_geometry = route_data.get('routes', [{}])[0].get('geometry')
    
    if not route_geometry:
        print("Error: Route geometry not found!")
        return []

    decoded_route = polyline.decode(route_geometry)

    total_distance_miles = route_data.get('routes', [{}])[0].get('summary', {}).get('distance', 0) / 1609.34  
    if total_distance_miles == 0:
        print("Error: Route distance not found!")
        return []

    current_mileage = 0  

    while current_mileage < total_distance_miles:
        next_stop_mileage = min(current_mileage + max_range, total_distance_miles)
        candidate_stations = []

        for station in fuel_stations:
            station_lat = station.get('lat')
            station_lon = station.get('lon')
            station_price = station.get('price')

            if station_lat is None or station_lon is None or station_price is None:
                continue  # Eksik veri varsa bu istasyonu geç

            for i in range(int(current_mileage), int(next_stop_mileage), 10):  
                if i < len(decoded_route):
                    route_point = decoded_route[i]
                    station_distance = haversine(route_point[0], route_point[1], station_lat, station_lon)
                    
                    if station_distance is not None and station_distance <= 5:  
                        candidate_stations.append(station)

        if candidate_stations:
            best_station = min(candidate_stations, key=lambda x: x['price'])
            optimal_stations.append(best_station)
            current_mileage = next_stop_mileage  
        else:
            current_mileage += 50  

    return optimal_stations




def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 3959  # Yer yarıçapı (mil cinsinden)
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # Sonuç mil cinsinden dönecek
    except Exception as e:
        print(f"Error in haversine calculation: {e}")
        return None


def calculate_fuel_cost(route_data, fuel_price_per_gallon):
    total_distance = sum(segment['distance'] for segment in route_data['routes'][0]['segments'])
    total_fuel_needed = total_distance / 1609.34 / 10  # Metreyi mile çevirdikten sonra galon
    return total_fuel_needed * fuel_price_per_gallon