import csv
import json
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from mainapp.sd_card import build_initial_flights, process_flights_post
from .forms import FlightForm
from .models import (
    Field_visualisation,
    Fields,
    Flight_Log,
    Flight_Paths,
    Sensor,
    SensorReading,
)
from .sd_card import SDCardError, detect_sd_cards
from collections import defaultdict
from datetime import date, timedelta
from django.db.models import Avg, Q

from .models import Field_visualisation, ZonalStat
from .data_visualisation import import_excel_to_db, build_chart_data, VARIABLES

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

flight_log_csv_path = os.path.join(settings.BASE_DIR, "Drone_Flying_Schedule_2025.csv")

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
    monday = today - timedelta(days=today.weekday())
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

    is_current_week = week_offset == 0

    context = {
        "week_num": week_num,
        "start_date": start_date,
        "end_date": end_date,
        "fields_status": fields_status,
        "week_offset": week_offset,
        "is_current_week": is_current_week,  
    }

    return render(request, "mainapp/weekly_overview.html", context)

logger = logging.getLogger("mainapp")

# regex to pull out your flight_path key from folder names
FOLDER_RE = re.compile(r'''
    ^(?:DJI_[0-9]{12}_[0-9]{3}_)?
    (?P<flight_path>\d+-[\w-]+-\d+m-[\w-]+(?:-\d+){0,2})
''', re.VERBOSE)

FlightFormSet = formset_factory(FlightForm, extra=0)

def discover_flights(dcim_root):
    for name in os.listdir(dcim_root):
        p = Path(dcim_root) / name
        if p.is_dir():
            m = FOLDER_RE.match(name)
            if m:
                yield p, m

def sd_card_view(request):
    sd_cards = []
    try:
        sd_cards = detect_sd_cards() or []
    except SDCardError:
        logger.warning("Failed to detect SD cards")

    selected = request.POST.get('sd_card', sd_cards[0] if sd_cards else None)

    if request.method == 'POST':
        logger.debug("POST keys: %s", list(request.POST.keys()))
        logger.debug("FILES keys: %s", list(request.FILES.keys()))
        formset = FlightFormSet(request.POST, request.FILES)

        for form in formset.forms:
            key = f"{form.prefix}-skyline_files"
            if not request.FILES.getlist(key):
                form.errors.pop('skyline_files', None)

        if formset.is_valid() and 'upload' in request.POST:
            total = process_flights_post(formset, selected, request)
            new_initial = build_initial_flights(selected)
            formset = FlightFormSet(initial=new_initial)
            messages.success(
                request, f"Done! Processed {total} flight{'s' if total != 1 else ''}."
            )
        else:
            messages.warning(request, f"There were errors: {formset.errors}")
    else:
        initial = build_initial_flights(selected)
        formset = FlightFormSet(initial=initial)

    return render(request, 'mainapp/sd_card.html', {
        'sd_cards': sd_cards,
        'selected_card': selected,
        'formset': formset,
    })




####################################################################
#data visualisation
####################################################################

def data_visualisation(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Last opp en Excel-fil (.xlsx).")
            return redirect("data_visualisation")
        try:
            created, changed = import_excel_to_db(file)
            messages.success(request, f"Importert: {created} nye, {changed} oppdatert/duplikater.")
        except Exception as e:
            messages.error(request, f"Import feilet: {e}")
        return redirect("data_visualisation")

    today = date.today()
    start_raw = request.GET.get("start_date")
    end_raw = request.GET.get("end_date")
    start_date = parse_date(start_raw) if isinstance(start_raw, str) and start_raw else (today - timedelta(days=30))
    end_date = parse_date(end_raw) if isinstance(end_raw, str) and end_raw else today

    field_name = request.GET.get("field") or ""
    specters_req = request.GET.getlist("specters")
    variables_req = request.GET.getlist("variables") or ["mean"]

    chart_data, selected_specters, selected_variables = build_chart_data(
        start_date, end_date, field_name, specters_req, variables_req
    )

    fields = list(Field_visualisation.objects.values_list("name", flat=True).order_by("name"))
    specters = list(ZonalStat.objects.values_list("spectrum", flat=True).distinct().order_by("spectrum"))

    return render(request, "mainapp/data_visualisation.html", {
        "fields": fields,
        "specters": specters,
        "variables": VARIABLES,
        "selected_specters": selected_specters,
        "selected_variables": selected_variables,
        "chart_data": chart_data,
    })



####################################################################
#review drone flights
####################################################################


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


####################################################################
#weekly overview
####################################################################


"""def folder_exists_for_week(base_path, start_date, end_date):
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

    return False"""


"""def weekly_view(request):
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

    return render(request, "mainapp/weekly.html", context)"""


####################################################################
#easygrowth
####################################################################


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


FILENAME_RE = re.compile(
    r"""
    ^\s*
    (?P<group>[^\s#]+)      
    (?:\s+.*?)?             
    \s*\#(?P<num>\d+)        
    (?:\s+JSON)?            
    \.txt\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

def parse_sensor_id_from_filename(filename: str) -> str:
    """
    Lager sensor_id i formatet 'GRUPPE #NUMMER' fra filnavn.
    Fallback: første ord i filnavnet (gammel oppførsel).
    Inneholder også en enkel normalisering fra '25BPROBARG20' -> '25PROBAR20'.
    """
    short = os.path.basename(filename)
    m = FILENAME_RE.match(short)
    if not m:
        base = os.path.splitext(short)[0]
        return (base.split()[0] if base.split() else base).strip()

    group = m.group("group").strip()
    num = int(m.group("num"))

    group = group.replace("BPROBARG", "PROBAR")

    return f"{group} #{num}"



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
            sensor_id = parse_sensor_id_from_filename(short_name)

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
