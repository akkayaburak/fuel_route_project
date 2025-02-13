from django.urls import path
from .views import calculate_route

urlpatterns = [
    path("calculate-route/", calculate_route, name="calculate_route"),
]
