from django.urls import path, include
from .views import list_fuel_stations
from .views import map_view

urlpatterns = [
    path('fuel-stations/', list_fuel_stations, name='list_fuel_stations'),
    path('map/', map_view, name='map'),
    path('api/', include('fuel_route.api.urls')),  # fuel_route/api/urls.py dosyasını dahil et
]
