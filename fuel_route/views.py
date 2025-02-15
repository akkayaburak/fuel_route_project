from django.http import JsonResponse
from .models import FuelStation
from django.shortcuts import render
from django.conf import settings


def list_fuel_stations(request):
    fuel_stations = FuelStation.objects.all().values("id","address", "city" ,"name", "price", "state", "lat", "lon",)
    return JsonResponse(list(fuel_stations), safe=False)


def map_view(request):
    return render(request, 'index.html',  {"mapbox_api_key": settings.MAPBOX_API_KEY})