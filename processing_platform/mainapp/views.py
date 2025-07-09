import csv
import datetime
import os
from datetime import date, datetime, timedelta

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.timezone import now

from .models import Fields, Flight, Flight_Log, Sensor, SensorReading
from .sd_card import detect_sd_cards


def home_view(request):
    return render(request, "mainapp/home.html")


def easy_growth(request):
    return render(request, "mainapp/easy_growth.html")


FIELD_FLIGHT_MODES = {
    "G2BOatFrontiers": ["3D", "MS"],
    "ProBarE166": ["3D", "MS"],
    "ProBarPilot": ["3D", "MS"],
    "ProBarSørås": ["3D", "MS"],
    "ProBarVoll": ["3D", "MS"],
    "RobOat": ["Thermal", "3D", "MS"],
    "SmartWheatBox": ["Thermal", "3D", "MS", "RGB"],
    "SmartWheatGram": ["Thermal", "3D", "MS"],
    "SmartWheatTunnel": ["Thermal", "3D", "MS", "RGB"],
    "Soldeling": ["Thermal", "3D", "MS"],
    "Vollebekk": ["RGB"],
}


def get_current_week_dates():
    today = date.today()
    monday = today - timedelta(days=today.weekday())  # Monday
    sunday = monday + timedelta(days=6)
    return monday, sunday


def weekly_overview(request):
    week_offset = int(request.GET.get("week_offset", 0))

    base_date = date.today() + timedelta(weeks=week_offset)
    start_date = base_date - timedelta(days=base_date.weekday())
    end_date = start_date + timedelta(days=6)
    week_num = start_date.isocalendar().week

    fields_status = []

    for field, flight_types in FIELD_FLIGHT_MODES.items():
        for flight_type in flight_types:
            logs = Flight_Log.objects.filter(
                flight_field_id=field,
                flight_type=flight_type,
                flight_date__range=(start_date, end_date),
            )

            flown = logs.exists()
            processed = logs.filter(p4d_processing="Yes").exists()

            status_level = 2 if flown and processed else 1 if flown else 0

            fields_status.append(
                {
                    "field": field,
                    "type": flight_type,
                    "flown": flown,
                    "processed": processed,
                    "status_level": status_level,
                }
            )

    # ✅ Add this line:
    is_current_week = week_offset == 0

    context = {
        "week_num": week_num,
        "start_date": start_date,
        "end_date": end_date,
        "fields_status": fields_status,
        "week_offset": week_offset,
        "is_current_week": is_current_week,  # 🔥 This enables your template check!
    }

    return render(request, "mainapp/weekly_overview.html", context)


def sd_card_view(request):
    sd_cards = detect_sd_cards()
    return render(request, "mainapp/sd_card.html", {"sd_cards": sd_cards})


def read_local_csv(request):
    # Replace <YourUsername> with your actual username or use os.path.expanduser
    downloads_path = os.path.expanduser("~/Downloads")
    csv_file_path = os.path.join(downloads_path, "Drone_Flying_Schedule_2025.csv")

    if not os.path.exists(csv_file_path):
        return JsonResponse(
            {"error": f"CSV file not found at {csv_file_path}"}, status=404
        )

    try:
        df = pd.read_csv(csv_file_path)
        data = df.to_dict(orient="records")
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def review_drone_flights(request):
    flights = []
    fields = [{"value": "all", "label": "All"}]
    flight_types = [{"value": "all", "label": "All"}]
    drone_pilots = [{"value": "all", "label": "All"}]

    # Get filters from GET request
    selected_field = request.GET.get("field", "all")
    selected_flight_type = request.GET.get("flight_type", "all")
    selected_drone_pilot = request.GET.get("drone_pilot", "all")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    # Start with all Flight_Log entries
    qs = Flight_Log.objects.all()

    # Apply filters conditionally
    if selected_field != "all":
        qs = qs.filter(flight_field_id=selected_field)
    if selected_flight_type != "all":
        qs = qs.filter(flight_type=selected_flight_type)
    if selected_drone_pilot != "all":
        qs = qs.filter(drone_pilot=selected_drone_pilot)
    if date_from:
        date_from_parsed = parse_date(date_from)
        if date_from_parsed:
            qs = qs.filter(flight_date__gte=date_from_parsed)
    if date_to:
        date_to_parsed = parse_date(date_to)
        if date_to_parsed:
            qs = qs.filter(flight_date__lte=date_to_parsed)

    flights = []

    for flight in qs:
        if isinstance(flight.flight_date, str):
            try:
                flight_date_obj = datetime.strptime(
                    flight.flight_date, "%d-%b-%Y"
                ).date()
            except Exception:
                flight_date_obj = None
        else:
            flight_date_obj = flight.flight_date

        flights.append(
            {
                "id": flight.id,
                "field": flight.flight_field_id,
                "date": flight_date_obj,
                "date_display": (
                    flight_date_obj.strftime("%B %d, %Y") if flight_date_obj else ""
                ),
                "image_type": flight.flight_type,
                "drone_pilot": flight.drone_pilot,
                "processing_status": flight.p4d_processing,
                "coordinates_correct": flight.p4d_step1_workable_data or "",
            }
        )

    # Dynamically build filter options from existing DB values
    unique_fields = Flight_Log.objects.values_list(
        "flight_field_id", flat=True
    ).distinct()
    unique_flight_types = Flight_Log.objects.values_list(
        "flight_type", flat=True
    ).distinct()
    unique_drone_pilots = Flight_Log.objects.values_list(
        "drone_pilot", flat=True
    ).distinct()

    fields += [{"value": f, "label": f} for f in sorted(filter(None, unique_fields))]
    flight_types += [
        {"value": f, "label": f} for f in sorted(filter(None, unique_flight_types))
    ]
    drone_pilots += [
        {"value": p, "label": p} for p in sorted(filter(None, unique_drone_pilots))
    ]

    context = {
        "flights": flights,
        "fields": fields,
        "flight_types": flight_types,
        "drone_pilots": drone_pilots,
        "selected_field": selected_field,
        "selected_flight_type": selected_flight_type,
        "selected_drone_pilot": selected_drone_pilot,
        "selected_date_from": date_from,
        "selected_date_to": date_to,
    }

    return render(request, "mainapp/review_drone_flights.html", context)


def flight_detail(request, flight_id):
    flight = get_object_or_404(Flight_Log, id=flight_id)

    # Flight_Log fields
    flight_fields = []
    for field in flight._meta.fields:
        name = field.verbose_name.title()
        value = field.value_from_object(flight)
        flight_fields.append((name, value))

    # Try to fetch related Fields instance by matching short_id
    field_data = Fields.objects.filter(long_id=flight.flight_field_id).first()

    field_fields = []
    if field_data:
        for field in field_data._meta.fields:
            name = field.verbose_name.title()
            value = field.value_from_object(field_data)
            field_fields.append((name, value))

    context = {
        "flight": flight,
        "flight_fields": flight_fields,
        "field_fields": field_fields,
    }
    return render(request, "mainapp/flight_detail.html", context)


def details_view(request):
    return render(request, "mainapp/details.html")


def add_routes_view(request):
    return render(request, "mainapp/add_routes.html")


def flight_events(request):
    events = []

    for flight in Flight.objects.all():
        color = "#00cc66" if flight.flown else "#ff6666"  # green if flown, red if not
        title = (
            f"{flight.title} - {flight.pilot.name if flight.pilot else 'Unassigned'}"
        )

        events.append(
            {
                "title": title,
                "start": flight.scheduled_time.isoformat(),
                "end": flight.end_time.isoformat(),
                "color": color,
                "extendedProps": {
                    "flown": flight.flown,
                    "pilot": flight.pilot.name if flight.pilot else None,
                    "frequency_days": flight.frequency_days,
                },
            }
        )
    return JsonResponse(events, safe=False)


def folder_exists_for_week(base_path, start_date, end_date):
    if not os.path.exists(base_path):
        return False

    try:
        for name in os.listdir(base_path):
            if len(name) >= 8 and name[:8].isdigit():
                try:
                    folder_date = datetime.datetime.strptime(name[:8], "%Y%m%d").date()
                    if start_date <= folder_date <= end_date:
                        return True
                except ValueError:
                    continue
    except PermissionError:
        return False

    return False


def weekly_view(request):
    csv_path = os.path.join(settings.BASE_DIR, "mainapp", "data", "flight_list.csv")
    all_flights = []

    # Get current week range
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_num = today.isocalendar()[1]

    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            field_name = row["Field folder name"].strip()
            flight_type = row["Type of flight"].strip()

            flown_path = row["1_flight path"].strip()
            processed_path = row["2_1_pix4d path"].strip()

            flown = folder_exists_for_week(flown_path, start_of_week, end_of_week)
            processed = folder_exists_for_week(
                processed_path, start_of_week, end_of_week
            )

            if not flown:
                status_level = 0  # red
            elif not processed:
                status_level = 1  # orange
            else:
                status_level = 2  # green

            all_flights.append(
                {
                    "field": field_name,
                    "type": flight_type,
                    "flown": flown,
                    "processed": processed,
                    "status_level": status_level,
                }
            )

    all_flights.sort(key=lambda x: x["status_level"])

    context = {
        "flights": all_flights,
        "week_num": week_num,
        "start_date": start_of_week,
        "end_date": end_of_week,
    }

    return render(request, "mainapp/weekly.html", context)


def parse_csv_datetime(datetime_string):
    """Trying to extract the date"""
    try:
        return datetime.strptime(datetime_string.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        return datetime.strptime(datetime_string.strip(), "%d.%m.%Y")


def process_csv_data(file_content, sensor_id):
    """reads csv files and puts the data into db, ignoring duplicates"""
    sensor, _ = Sensor.objects.get_or_create(sensor_id=sensor_id)

    decoded = file_content.decode("utf-8").splitlines()
    reader = csv.reader(decoded)

    try:
        header = next(reader)
    except StopIteration:
        return

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

            SensorReading.objects.get_or_create(
                sensor=sensor, timestamp=timestamp, defaults=reading_data
            )

        except Exception as e:
            print(f"Feil i rad {row}: {e}")
            continue


def upload_easy_growth_data(request):
    """Hovedvisningen for å laste opp sensorfiler fra brukerens maskin."""
    if request.method == "POST":
        source = request.POST.get("source")

        if source == "files":
            files = request.FILES.getlist("files")
        elif source == "folder":
            files = request.FILES.getlist("folder_files")
        else:
            files = []

        if not files:
            messages.error(request, "Ingen filer valgt.")
            return redirect(request.path)

        total = 0
        for file in files:
            filename_parts = (
                file.name.split("/") if "/" in file.name else file.name.split("\\")
            )
            short_name = filename_parts[-1]

            sensor_id = short_name.split()[0].strip()

            try:
                process_csv_data(file.read(), sensor_id)
                total += 1
            except Exception as e:
                print(f"Feil i fil: {file.name} – {e}")

        messages.success(request, f"{total} filer behandlet.")
        return redirect(request.path)

    return render(request, "mainapp/flight_details.html")
