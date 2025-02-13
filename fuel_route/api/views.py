from django.http import JsonResponse
from fuel_route.models import FuelStation
from django.views.decorators.csrf import csrf_exempt
import os
import requests
import polyline
from math import radians, sin, cos, sqrt, atan2


ORS_API_KEY = os.getenv('ORS_API_KEY')

@csrf_exempt
def calculate_route(request):
    start_lat = 40.712776  # New York
    start_lon = -74.005974
    end_lat = 38.9072  # Washington DC
    end_lon = -77.0369
    
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
        
        # Yakıt istasyonlarını listele
        fuel_stations = list(FuelStation.objects.all().values())
        
        # Optimum yakıt istasyonlarını al
        optimal_stations = get_optimal_fuel_stations(route_data, fuel_stations)
        
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
    
    # Rota geometrisini al
    route_geometry = route_data['routes'][0]['geometry']
    decoded_route = polyline.decode(route_geometry)
    
    # Yakıt istasyonlarının mesafelerini hesapla
    for station in fuel_stations:
        # Her bir yakıt istasyonu ile rota arasındaki mesafeyi hesapla
        min_distance = float('inf')
        
        # Rotadaki her bir nokta için mesafeyi hesapla
        for point in decoded_route:
            distance_to_route = haversine(point[0], point[1], station['lat'], station['lon'])
            if distance_to_route and distance_to_route < min_distance:
                min_distance = distance_to_route
        
        # Mesafe None ise geç
        if min_distance is None or min_distance > 5:
            continue
        
        # Eğer istasyon rota güzergahına yakınsa (5 mil içinde)
        optimal_stations.append(station)

    # İstasyonları mesafeye göre sıralama (en yakın istasyon önce gelsin)
    optimal_stations.sort(key=lambda x: min([haversine(point[0], point[1], x['lat'], x['lon']) for point in decoded_route]), reverse=False)
    
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
    total_distance = 0
    
    # Segmentlerdeki mesafeyi topla
    for segment in route_data['routes'][0]['segments']:
        total_distance += segment['distance']
    
    # Toplam galon hesabı
    total_fuel_needed = total_distance / 10  # galon cinsinden
    total_cost = total_fuel_needed * fuel_price_per_gallon
    
    return total_cost
