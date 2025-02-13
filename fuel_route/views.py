from django.http import JsonResponse
from .models import FuelStation

def list_fuel_stations(request):
    fuel_stations = FuelStation.objects.all().values("id","address", "city" ,"name", "price", "state", "lat", "lon",)
    return JsonResponse(list(fuel_stations), safe=False)
