import os
from django.conf import settings
import csv
from datetime import datetime
from django.shortcuts import render

sensor_data_path = "P:\PheNo\easy_growth_data"


def parse_csv_date(datestring):
    return datetime.strptime(datestring.split(",")[0].strip(), "%d.%m.%Y")


def upload_easy_growth_data(request):
    if request.method == "POST":
        files = request.FILES.getlist("files")

        uploaded_files = []
        for file in files:
            sensor_field = file.name.split()[0]
            sensor_path = os.path.join(sensor_data_path, sensor_field)
            os.makedirs(sensor_path, exist_ok=True)
            file_path = sensor_path = os.path.join(sensor_path, file.name)
            os.makedirs(file_path, exist_ok=True)

            decoded_lines = file.read().decode("utf-8").splitlines()
            reader = list(csv.reader(decoded_lines))
            header, *rows = reader

            if not rows:
                continue

            start_date = parse_csv_date(rows[-1][0])
            end_date = parse_csv_date(rows[0][0])

            filename = f"{file.name}__{start_date}_{end_date}"
            file_destination = os.path.join(file_path, filename)
            file.seek(0)

            with open(file_destination, "w") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)


def api_easy_growth_data():
    return 0
