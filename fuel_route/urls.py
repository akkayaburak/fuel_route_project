from django.urls import path, include

urlpatterns = [
    path('api/', include('fuel_route.api.urls')),  # fuel_route/api/urls.py dosyasını dahil et
]
