import os
import csv
from datetime import datetime
from django.shortcuts import render
from django.db import IntegrityError
from .models import Sensor, SensorReading

sensor_data_path = "P:\\PheNo\\easy_growth_data"


def parse_csv_date(datestring):
    return datetime.strptime(datestring.strip(), "%d.%m.%Y")


def parse_csv_datetime(datetime_string):
    try:
        return datetime.strptime(datetime_string.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        return datetime.strptime(datetime_string.strip(), "%d.%m.%Y")


def upload_easy_growth_data(request):
    if request.method == "POST":
        files = request.FILES.getlist("files")
        uploaded_files = []

        for file in files:
            sensor_id = file.name.split()[0].strip()
            sensor, created = Sensor.objects.get_or_create(sensor_id=sensor_id)

            decoded_lines = file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_lines)
            header = next(reader)

            for row in reader:
                if not row or not row[0].strip():
                    continue

                try:
                    timestamp = parse_csv_datetime(row[0])

                    reading_data = {
                        "soil_temperature": float(row[1]) if row[1] else None,
                        "soil_moisture": float(row[2]) if row[2] else None,
                        "air_temperature": float(row[3]) if row[3] else None,
                        "air_humidity": float(row[4]) if row[4] else None,
                        "battery": float(row[5]) if row[5] else None,
                        "rainfall": float(row[6]) if row[6] else None,
                        "crop_type": row[7].strip() if len(row) > 7 else "",
                        "soil_type": row[8].strip() if len(row) > 8 else "",
                    }

                    obj, created = SensorReading.objects.get_or_create(
                        sensor=sensor, timestamp=timestamp, defaults=reading_data
                    )
                    if created:
                        print(f"Opprettet reading for {sensor_id} @ {timestamp}")
                    else:
                        print(f"Hoppet over duplikat: {sensor_id} @ {timestamp}")
                except Exception as e:
                    print(f"Feil ved behandling av rad: {row} – {e}")

        return render(request, "upload_success.html")
    return render(request, "upload_form.html")
