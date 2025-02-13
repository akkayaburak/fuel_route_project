from django.db import models

class FuelStation(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    retail_price = models.DecimalField(max_digits=5, decimal_places=3)
    lat = models.FloatField()
    lon = models.FloatField()

    def __str__(self):
        return self.name


class Route(models.Model):
    start_lat = models.FloatField()
    start_lon = models.FloatField()
    end_lat = models.FloatField()
    end_lon = models.FloatField()
    total_cost = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Route from ({self.start_lat}, {self.start_lon}) to ({self.end_lat}, {self.end_lon})"
