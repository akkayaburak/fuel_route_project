# fuel_route/management/commands/update_fuel_stations.py
import csv
import os
import time
from django.core.management.base import BaseCommand
from fuel_route.models import FuelStation
from fuel_route.geocoding import get_lat_lon_from_address

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE_DIR, "management", "commands", "data", "fuel-prices-for-be-assessment.csv")

class Command(BaseCommand):
    help = "Update fuel stations with latitude and longitude from the CSV file"

    def handle(self, *args, **kwargs):
        with open(CSV_PATH, "r") as file:
            reader = csv.DictReader(file)
            total = sum(1 for _ in reader)  # Find total row number
            file.seek(0)  # Get back to head
            next(reader)  # Pass the header

            for i, row in enumerate(reader, start=1):
                name = row["Truckstop Name"]
                address = row["Address"]
                city = row["City"]
                state = row["State"]
                price = float(row["Retail Price"])

                # Get lan/lon from Mapbox
                lat, lon = get_lat_lon_from_address(address, city, state)

                if lat is None or lon is None:
                    print(f"⚠️ {name} için konum bulunamadı, atlanıyor...")
                    continue  # Don't save it if there is no Lat/Lon 

                # Save it to db
                FuelStation.objects.create(
                    name=name,
                    address=address,
                    city=city,
                    state=state,
                    price=price,
                    lat=lat,
                    lon=lon
                )

                print(f"✅ [{i}/{total}] {name} ({city}, {state}) saved: {lat}, {lon}")
                # Waiting for 0.2 sec for API rates
                time.sleep(0.2)

        print("🔥 All fuel stations successfully updated")
