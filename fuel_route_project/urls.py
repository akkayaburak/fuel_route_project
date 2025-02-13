from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('fuel/', include('fuel_route.urls')),  # fuel_route app'inin URL'lerini dahil ettik
]
