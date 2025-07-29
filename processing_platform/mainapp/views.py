from django.shortcuts import render
import logging
logger = logging.getLogger(__name__)
import csv
import json
import os
from datetime import date, datetime, timedelta
import pandas as pd
import shutil
import re
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.utils import timezone
from .models import Fields, Flight_Log, SensorReading, Sensor
from .sd_card import detect_sd_cards

logger = logging.getLogger(__name__)

# Base output root; ensure this is accessible on your system
BASE_OUTPUT = os.path.expanduser('~/PheNo')

# Regex to extract the Flight Path Name portion of an SD-card folder
FOLDER_RE = re.compile(r'''
    ^(?:DJI_[0-9]{12}_[0-9]{3}_)?   # optional DJI_YYYYMMDDhhmm_###_
    (?P<flight_path>
        \d+                        # flight‐path ID, e.g. '25'
        -[\w-]+                    # site name, e.g. 'RobOat' (allows letters, digits, underscores, hyphens)
        -\d+m                      # altitude, e.g. '20m'
        -[\w-]+                    # flight angle, e.g. 'Oblique'
        -\d+                       # start tilt, e.g. '80'
        -\d+                       # end tilt, e.g. '85'
    )
    (?:\..*)?$                     # optional extension or trailer
''', re.VERBOSE)


def home_view(request):
    print(">>> ENTER home_view")
    logger.debug("ENTER home_view")
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
    print(">>> ENTER sd_card_view, method:", request.method)
    logger.debug("⇒ Enter sd_card_view; method=%s", request.method)

    sd_cards = detect_sd_cards()
    print(">>> detect_sd_cards returned:", sd_cards)
    logger.debug("Detected SD cards: %r", sd_cards)

    # Hard-code drone models here, because the CSV is wrong
    # Pull the machine-readable values from your Flight_Log model
    drone_models = [choice[0] for choice in Flight_Log.DRONE_MODEL_CHOICES]
    print(">>> available drone_models:", drone_models)
    logger.debug("Available drone models: %r", drone_models)

    if request.method == 'POST':
        print(">>> sd_card_view handling POST, data:", dict(request.POST))
        logger.debug("Handling POST; POST data=%r", request.POST)

        sd_card_dcim   = request.POST.get('sd_card')
        selected_drone = request.POST.get('drone_model')
        print(">>> POST values:", sd_card_dcim, selected_drone)
        logger.debug(" sd_card_dcim=%r, selected_drone=%r", sd_card_dcim, selected_drone)

        if not sd_card_dcim:
            messages.error(request, "Please pick an SD card.")
            return redirect('sd_card')
        if not selected_drone:
            messages.error(request, "Please select a drone model.")
            return redirect('sd_card')

        copied = 0
        os.makedirs(BASE_OUTPUT, exist_ok=True)
        print(">>> ensured BASE_OUTPUT exists:", BASE_OUTPUT)
        logger.debug("Ensured BASE_OUTPUT exists: %s", BASE_OUTPUT)

        for sub in os.listdir(sd_card_dcim):
            print(">>> iterating folder:", sub)
            logger.debug("Found entry in SD card: %s", sub)

            src = os.path.join(sd_card_dcim, sub)
            if not os.path.isdir(src):
                print(">>> skipping non-dir:", sub)
                logger.debug("Skipping non-directory: %s", sub)
                continue

            m = FOLDER_RE.match(sub)
            if not m:
                print(">>> regex did not match:", sub)
                logger.warning("Skipping folder with unexpected name: %r", sub)
                continue

            flight_path_key = m.group('flight_path')
            print(">>> flight_path_key:", flight_path_key)
            logger.debug("Regex matched flight_path_key=%r", flight_path_key)

            try:
                fp = Flight_Paths.objects.get(
                    flight_path_name__startswith=flight_path_key
                )
                print(">>> found Flight_Paths:", fp)
                logger.debug("Found Flight_Paths entry: %r", fp)
            except Flight_Paths.DoesNotExist:
                print(">>> no Flight_Paths matching:", flight_path_key)
                logger.warning("No DB entry matching Flight Path Name %r", flight_path_key)
                continue
            except Flight_Paths.MultipleObjectsReturned:
                print(">>> multiple Flight_Paths matching:", flight_path_key)
                logger.warning("Multiple entries match Flight Path Name %r", flight_path_key)
                continue

            today_str = date.today().strftime('%Y%m%d')
            side      = str(int(fp.side_overlap)) if fp.side_overlap is not None else ''
            front     = str(int(fp.front_overlap)) if fp.front_overlap is not None else ''
            # Use spaces between all components, no semicolons
            parts = [today_str, fp.short_id, selected_drone, fp.type_of_flight, side, front]
            new_folder = ' '.join(p for p in parts if p)
            print(">>> new_folder name:", new_folder)
            logger.debug("New folder name: %s", new_folder)

            dest_root = fp.first_flight_path
            if not dest_root:
                print(">>> fp.first_flight_path missing for:", fp)
                logger.error("No first_flight_path defined for %r", fp.flight_path_name)
                continue

            dest = os.path.join(dest_root, new_folder)
            os.makedirs(dest, exist_ok=True)
            print(">>> ensured dest exists:", dest)
            logger.debug("Ensured destination exists: %s", dest)

            try:
                print(f">>> copying {src} → {dest}")
                logger.debug("Copying %r → %r …", src, dest)
                shutil.copytree(src, dest, dirs_exist_ok=True)

                copied += 1
                print(">>> copied count:", copied)
                logger.info("Copied %r → %r (total copied=%d)", src, dest, copied)

            except Exception as exc:
                print(">>> copy failed:", exc)
                logger.error("Failed to copy %r: %s", src, exc)
                messages.error(request, f"Failed to copy {sub}: {exc}")

        messages.success(request, f"Copied {copied} folders into {BASE_OUTPUT}.")
        return redirect('sd_card')

    return render(request, 'mainapp/sd_card.html', {
        'sd_cards': sd_cards,
        'drone_models': drone_models,
        'selected_drone': None,
    })

"""def data_visualisation_view(request):
    return render(request, 'mainapp/data_visualisation.html')"""

STAT_OPTIONS = [

    ("cv", "Coefficient of Variation"),
    ("iqr", "Interquartile Range"),
    ("kurtosis", "Kurtosis"),
    ("majority", "Majority"),
    ("max", "Maximum"),
    ("mean", "Mean"),
    ("median", "Median"),
    ("min", "Minimum"),
    ("minority", "Minority"),
    ("q25", "25th Percentile (Q1)"),
    ("q75", "75th Percentile (Q3)"),
    ("range", "Range (Max - Min)"),
    ("std", "Standard Deviation"),
    ("sum", "Sum"),
    ("top_10", "Top 10 Values"),
    ("top_10_mean", "Mean of Top 10 Values"),
    ("skewness", "Skewness"),
]

def data_visualisation(request):
    selected_stats = request.GET.getlist("stats")
    selected_dates = request.GET.getlist("date")
    
    all_dates = []
    downloads_path = os.path.expanduser("~/Downloads")
    csv_file_path = os.path.join(downloads_path, "24BPROBARG20_Vollebekk_2024.csv")

    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path)
        if "date" in df.columns:
            all_dates = (
                pd.to_datetime(df["date"], errors="coerce")
                .dt.strftime("%Y-%m-%d")
                .drop_duplicates()
                .sort_values()
                .tolist()
            )

    plots = []
    return render(request, "mainapp/data_visualisation.html", {
        "plots": plots,
        "stat_options": STAT_OPTIONS,
        "selected_stats": selected_stats,
        "selected_dates": selected_dates,
        "all_dates": all_dates,
    })

df = pd.read_csv("~/Downloads/Drone_Flying_Schedule_2025.csv")
print(df.columns)  # See what columns actually exist

def read_local_csv(request):
    print(">>> ENTER read_local_csv")
    logger.debug("ENTER read_local_csv")
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

def read_local_csv(request):
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
    today = date.today()
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

def process_json_data(json_data, sensor_id):
    """Lagrer rader fra en JSON-fil i databasen."""
    sensor, _ = Sensor.objects.get_or_create(sensor_id=sensor_id)
    total = 0
    added = 0

    for entry in json_data:
        try:
            timestamp_str = entry["TS"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")

            reading_data = {
                "soil_temperature": float(entry["JT"]) if entry.get("JT") else None,
                "soil_moisture": float(entry["JF"]) if entry.get("JF") else None,
                "air_temperature": float(entry["LT"]) if entry.get("LT") else None,
                "air_humidity": float(entry["LF"]) if entry.get("LF") else None,
                "battery": float(entry["BT"]) if entry.get("BT") else None,
                "rainfall": float(entry["R"]) if entry.get("R") else None,
                "crop_type": entry.get("crop", "").strip(),
                "soil_type": entry.get("soilType", "").strip(),
            }

            obj, created = SensorReading.objects.get_or_create(
                sensor=sensor,
                timestamp=timestamp,
                defaults=reading_data,
            )
            if created:
                added += 1
            total += 1

        except Exception as e:
            logger.error(f"Error json row {entry}: {e}")
            continue




def process_json_data(json_data, sensor_id):
    """Lagrer rader fra en JSON-fil i databasen."""
    sensor, _ = Sensor.objects.get_or_create(sensor_id=sensor_id)
    added = 0

    for entry in json_data:
        try:
            timestamp_str = entry["TS"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")

            reading_data = {
                "soil_temperature": float(entry["JT"]) if entry.get("JT") else None,
                "soil_moisture": float(entry["JF"]) if entry.get("JF") else None,
                "air_temperature": float(entry["LT"]) if entry.get("LT") else None,
                "air_humidity": float(entry["LF"]) if entry.get("LF") else None,
                "battery": float(entry["BT"]) if entry.get("BT") else None,
                "rainfall": float(entry["R"]) if entry.get("R") else None,
                "crop_type": entry.get("crop", "").strip(),
                "soil_type": entry.get("soilType", "").strip(),
            }

            _, created = SensorReading.objects.get_or_create(
                sensor=sensor,
                timestamp=timestamp,
                defaults=reading_data,
            )
            if created:
                added += 1

        except Exception as e:
            logger.error(f"Feil i JSON-rad {entry}: {e}")
            continue

    logger.info(f"Sensor {sensor_id}: {added}/{len(json_data)} rader lagt til.")



def upload_easy_growth_data(request):
    sensors = Sensor.objects.all()
    chart_data = []
    latest_reading = None
    default_end = timezone.now().date()
    default_start = default_end - timedelta(days=14)

    selected_sensor_id = request.GET.get("sensor")
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")
    try:
        if start_str:
            default_start = datetime.strptime(start_str, "%Y-%m-%d").date()
        if end_str:
            default_end = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Ugyldig datoformat.")
        return redirect(request.path)

    if selected_sensor_id:
        readings = SensorReading.objects.filter(
            sensor__sensor_id=selected_sensor_id,
            timestamp__date__range=(default_start, default_end)
        ).order_by("timestamp")

        chart_data = [
            {
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
                "air_temperature": r.air_temperature,
                "soil_temperature": r.soil_temperature,
                "air_humidity": r.air_humidity,
                "soil_moisture": r.soil_moisture,
            }
            for r in readings
        ]
        latest_reading = readings.last()

    if request.method == "POST":
        files = request.FILES.getlist("files")
        total = 0
        for file in files:
            short_name = file.name.split("/")[-1].split("\\")[-1]
            sensor_id = short_name.split()[0].strip()

            try:
                data = json.loads(file.read().decode("utf-8"))
                process_json_data(data, sensor_id)
                total += 1
            except Exception as e:
                logger.error(f"Error handling file {file.name}: {e}")
                messages.error(request, f"Feil i fil: {file.name}")

        if total:
            messages.success(request, f"{total} fil(er) lastet opp.")
        return redirect(request.path)

    return render(request, "mainapp/easy_growth.html", {
        "sensors": sensors,
        "chart_data": chart_data,
        "latest_readings": latest_reading,
        "default_start": default_start.isoformat(),
        "default_end": default_end.isoformat(),
    })