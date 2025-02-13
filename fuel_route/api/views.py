import requests
from django.http import JsonResponse
from fuel_route.models import FuelStation
from django.views.decorators.csrf import csrf_exempt
import os
from geopy.distance import geodesic
import polyline

ORS_API_KEY = os.getenv('ORS_API_KEY')

@csrf_exempt
def calculate_route(request):
    start_lat = 40.712776 #new york
    start_lon = -74.005974
    end_lat = 38.9072 #dc
    end_lon = -77.0369
    
    # OpenRouteService API çağrısını yap
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
        
        # Toplam maliyeti hesapla
        total_cost = calculate_fuel_cost(route_data, 3.50)  # 3.50 USD/gallon örneği
        
        # Sonuçları döndür
        return JsonResponse({
            "route": route_data,
            "optimal_fuel_stations": optimal_stations,
            "total_fuel_cost": total_cost
        })
    else:
        return JsonResponse({"error": "Error fetching route data from ORS"}, status=500)


def get_optimal_fuel_stations(route_data, fuel_stations):
    optimal_stations = []
    
    # OpenRouteService cevabının doğruluğunu kontrol et
    if 'routes' not in route_data or len(route_data['routes']) == 0:
        print("No routes found in the response!")
        return optimal_stations
    
    route_geometry = route_data['routes'][0].get('geometry', None)
    if not route_geometry:
        print("No geometry found in the route data!")
        return optimal_stations
    
    # Polyline'ı çözümle
    try:
        coordinates = polyline.decode(route_geometry)  # Polyline çözümlemesi
    except Exception as e:
        print(f"Error decoding polyline: {e}")
        return optimal_stations
    
    # Yakıt istasyonlarını kontrol et
    for station in fuel_stations:
        station_location = (station['lat'], station['lon'])
        
        # Polyline'daki her noktayı kontrol et
        for i in range(0, len(coordinates), int(len(coordinates) / 10)):
            route_point = (coordinates[i][0], coordinates[i][1])  # [lat, lon] formatı
            distance = geodesic(station_location, route_point).miles
            
            # Eğer istasyon rota güzergahına yakınsa (örneğin 5 mil içinde)
            if distance <= 5:
                optimal_stations.append(station)
                break  # Bir kez eklendiyse, tekrar eklememek için kırıyoruz
    
    return optimal_stations



def calculate_fuel_cost(route_data, fuel_price_per_gallon):
    total_distance = 0
    
    for segment in route_data['routes'][0]['segments']:
        for step in segment['steps']:
            total_distance += step['distance']
    
    total_fuel_needed = total_distance / 10  # galon cinsinden
    total_cost = total_fuel_needed * fuel_price_per_gallon
    
    return total_cost
