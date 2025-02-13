from django.urls import path, include
from .views import list_fuel_stations

urlpatterns = [
    path('fuel-stations/', list_fuel_stations, name='list_fuel_stations'),
    path('api/', include('fuel_route.api.urls')),  # fuel_route/api/urls.py dosyasını dahil et
]
