import os
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
import requests

ORS_API_KEY = os.getenv('ORS_API_KEY')

@csrf_exempt
def calculate_route(request):
    if request.method == "POST":
        data = json.loads(request.body)
        start_lat = data.get("start_lat")
        start_lon = data.get("start_lon")
        end_lat = data.get("end_lat")
        end_lon = data.get("end_lon")

        # OpenRouteService API URL
        ors_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        
        # OpenRouteService API'ye istek gönderme
        payload = {
            "coordinates": [
                [start_lon, start_lat],  # Start point
                [end_lon, end_lat]  # End point
            ]
        }
        
        headers = {
            "Authorization": ORS_API_KEY
        }

        response = requests.post(ors_url, json=payload, headers=headers)

        if response.status_code == 200:
            route_data = response.json()
            # Burada rota verisini işleyebiliriz.
            return JsonResponse(route_data)
        else:
            return JsonResponse({"error": "Error fetching route from ORS"}, status=500)
        
    return JsonResponse({"error": "Invalid request"}, status=400)
