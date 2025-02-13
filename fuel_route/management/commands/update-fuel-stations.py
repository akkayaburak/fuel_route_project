# fuel_route/management/commands/update_fuel_stations.py
import csv
from django.core.management.base import BaseCommand
from fuel_route.models import FuelStation
from fuel_route.geocoding import get_lat_lon_from_address
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Command(BaseCommand):
    help = 'Update fuel stations with latitude and longitude from the CSV file'

    def handle(self, *args, **kwargs):
        csv_file = os.path.join(BASE_DIR, "management", "commands","data", "fuel-prices-for-be-assessment.csv")

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['Truckstop Name']
                address = row['Address']
                city = row['City']
                state = row['State']
                price = float(row['Retail Price'])

                lat, lon = get_lat_lon_from_address(address)

                FuelStation.objects.create(
                    name=name,
                    address=address,
                    city=city,
                    state=state,
                    price=price,
                    lat=lat,
                    lon=lon
                )

        self.stdout.write(self.style.SUCCESS('Yakıt istasyonları başarıyla güncellendi!'))
