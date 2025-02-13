import csv
from django.core.management.base import BaseCommand
from fuel_route.models import FuelStation
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = "Import fuel station data from CSV file"

    def handle(self, *args, **kwargs):
        csv_file = os.path.join(BASE_DIR, "management", "commands","data", "fuel-prices-for-be-assessment.csv")
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                FuelStation.objects.create(
                    name=row["Truckstop Name"],
                    address=row["Address"],
                    city=row["City"],
                    state=row["State"],
                    price=float(row["Retail Price"]),
                )
        self.stdout.write(self.style.SUCCESS("Fuel stations imported successfully!"))
