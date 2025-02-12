from django.db import models

class FuelStop(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    retail_price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"
