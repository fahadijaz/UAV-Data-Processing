import csv
import json
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db.models import Avg, Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import FlightForm
from .models import (
    FieldVisualisation,
    Fields,
    Flight_Log,
    Flight_Paths,
    Sensor,
    SensorReading,
    Spectrum,
    ZonalStat,
)
from .sd_card import (
    SDCardError,
    detect_sd_cards,
    build_initial_flights,
    process_flights_post,
    FlightFormSet,
)
from .data_visualisation import (
    import_excel_to_db,
    VARIABLES,
    build_chart_data,
)

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


def sd_card_view(request):
    """
    Main view for SD card flight processing.
    Detects connected SD cards, discovers valid DJI flight folders,
    and builds pre-filled flight forms for user review.
    On submission, copies flight data (and optional reflectance/skyline images),
    and creates corresponding Flight_Log database entries.
    """
    try:
        sd_cards = detect_sd_cards()
        print(f"Detected SD cards: {sd_cards}")
    except SDCardError:
        sd_cards = []
        messages.warning(request, "No SD cards detected.")
    
    selected = request.POST.get('sd_card') or request.GET.get('selected_dcim')
    if not selected and sd_cards:
        selected = sd_cards[0]
    
    formset = None
    pilot_choices = [('', 'Select Pilot')] + Flight_Log.DRONE_PILOT_CHOICES
    drone_model_choices = [('', 'Select Model')] + Flight_Log.DRONE_MODEL_CHOICES
    
    if request.method == 'POST' and selected:
        dcim_path = selected
        if os.path.exists(dcim_path):
            initial_flights = build_initial_flights(dcim_path)
            if initial_flights:
                formset = FlightFormSet(request.POST, request.FILES, initial=initial_flights)
                processed = process_flights_post(formset, selected, request)
                if processed:
                    messages.success(request, f"Successfully processed {processed} flights.")
                else:
                    messages.error(request, "Failed to process flights.")
            else:
                messages.warning(request, "No flights detected on that card. Make sure the SD card contains flight folders with the expected naming pattern.")
        else:
            messages.error(request, "No DCIM folder found on the selected SD card.")
        return redirect("sd_card_view")
    
    if selected and os.path.exists(selected):
        initial_flights = build_initial_flights(selected)
        if initial_flights:
            formset = FlightFormSet(initial=initial_flights)
            print(f"Found {len(initial_flights)} flights: {[f['flight_path_key'] for f in initial_flights]}")
        else:
            print("No flights found matching the expected pattern")
    
    print(f"Passing to template - sd_cards: {sd_cards}, selected: {selected}")
    return render(request, "mainapp/sd_card.html", {
        "sd_cards": sd_cards,
        "selected_dcim": selected,
        "formset": formset,
        "pilot_choices": pilot_choices,
        "drone_model_choices": drone_model_choices,
    })


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
    ("skewness", "Skewness"),
    ("std", "Standard Deviation"),
    ("sum", "Sum"),
    ("top_10", "Top 10 Values"),
    ("top_10_mean", "Mean of Top 10 Values"),
    ("top_10_median", "Median of Top 10 Values"),
    ("top_10_std", "Standard Deviation of Top 10 Values"),
    ("top_15", "Top 15 Values"),
    ("top_15_mean", "Mean of Top 15 Values"),
    ("top_15_median", "Median of Top 15 Values"),
    ("top_15_std", "Standard Deviation of Top 15 Values"),
    ("top_20", "Top 20 Values"),
    ("top_25", "Top 25 Values"),
    ("top_25_mean", "Mean of Top 25 Values"),
    ("top_25_median", "Median of Top 25 Values"),
    ("top_25_std", "Standard Deviation of Top 25 Values"),
    ("top_35", "Top 35 Values"),
    ("top_35_mean", "Mean of Top 35 Values"),
    ("top_35_median", "Median of Top 35 Values"),
    ("top_35_std", "Standard Deviation of Top 35 Values"),
    ("top_50", "Top 50 Values"),
    ("top_50_mean", "Mean of Top 50 Values"),
    ("top_50_median", "Median of Top 50 Values"),
    ("top_50_std", "Standard Deviation of Top 50 Values"),
    ("top_5_mean", "Mean of Top 5 Values"),
    ("top_5_median", "Median of Top 5 Values"),
    ("top_5_std", "Standard Deviation of Top 5 Values"),
    ("variance", "Variance"),
    ("variety", "Variety (Number of Unique Values)"),
]


def data_visualisation(request):
    """
    Handle data visualization for field spectra.

    Behavior
    --------
    - POST:
        Accepts an uploaded Excel (.xlsx) file, imports its rows into the database
        via `import_excel_to_db(file)`, and reports back using Django messages.
        Always redirects to the same view afterward (PRG pattern).

    - GET:
        Reads filters from query params:
          * start_date / end_date : ISO date (YYYY-MM-DD); defaults to last 30 days
          * field                 : FieldVisualisation.name (optional)
          * specters              : one or more spectrum names (case-insensitive)
          * variables             : one or more metric names; defaults to ["mean"]
        Builds `chart_data` by calling `build_chart_data(...)`, which returns
        arrays of raw values per (date × specter × variable) suitable for a boxplot.
        Renders the template `mainapp/data_visualisation.html` with dropdown
        options and a JSON payload (`chart_data_json`) consumed by the frontend.

    Template context
    ----------------
    - fields              : list[str] of FieldVisualisation names for the field selector
    - specters            : list[str] of available spectrum names for the specter selector
    - variables           : list[str] of supported variable names (from `VARIABLES`)
    - selected_specters   : list[str] reflecting the active specter filter
    - selected_variables  : list[str] reflecting the active variable filter
    - chart_data_json     : JSON string with:
        {
          "dates":  ["YYYY-MM-DD", ...],
          "series": [
            {"name": "<specter> · <variable>", "data": [ [values on date0], [values on date1], ... ]},
            ...
          ]
        }

    Notes
    -----
    - `specters` and `variables` accept multiple values via repeated query params.
    - Messages are shown in Norwegian to match the rest of the UI.
    - No exceptions are raised to the user; errors are surfaced via Django messages.
    """

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
    start_date = parse_date(start_raw) if start_raw else (today - timedelta(days=30))
    end_date = parse_date(end_raw) if end_raw else today

    field_name = request.GET.get("field") or ""
    specters_req = [s.strip().lower() for s in request.GET.getlist("specters")]
    variables_req = request.GET.getlist("variables") or ["mean"]

    chart_data, selected_specters, selected_variables = build_chart_data(
        start_date, end_date, field_name, specters_req, variables_req
    )

    fields = list(FieldVisualisation.objects.values_list("name", flat=True).order_by("name"))
    specters = list(Spectrum.objects.values_list("name", flat=True).distinct().order_by("name"))

    return render(request, "mainapp/data_visualisation.html", {
        "fields": fields,
        "specters": specters,
        "variables": VARIABLES,
        "selected_specters": selected_specters,
        "selected_variables": selected_variables,
        "chart_data_json": json.dumps(chart_data), 
    })


####################################################################
# Review drone flights
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
# Easy Growth
####################################################################


def process_json_data(json_data, sensor_id):
    """
    Persist readings from a JSON payload for a single sensor.

    Parameters
    ----------
    json_data : list[dict]
        Iterable where each entry is one reading. Expected keys:
          - "TS": ISO-8601 timestamp, e.g. "2024-01-02T03:04:05.678Z" (required)
          - "JT" -> soil_temperature (optional, numeric)
          - "JF" -> soil_moisture   (optional, numeric)
          - "LT" -> air_temperature (optional, numeric)
          - "LF" -> air_humidity    (optional, numeric)
          - "BT" -> battery         (optional, numeric)
          - "R"  -> rainfall        (optional, numeric)
          - "crop"     -> crop_type     (optional, string)
          - "soilType" -> soil_type     (optional, string)
    sensor_id : str
        Normalized sensor identifier. The Sensor row is created on demand.

    Behavior
    --------
    - Uses (sensor, timestamp) as a natural key via get_or_create to avoid duplicates.
    - On insert, sets the parsed fields; existing rows are left unchanged.
    - Logs per-row parse errors and continues with the rest.
    - Logs a final summary: <added>/<total> rows inserted.
    """
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
    Generates a sensor_id from the filename in the format 'GROUP #NUMBER'.
    Fallback: uses the first word of the filename (legacy behavior).
    Also applies a simple normalization: '25BPROBARG20' -> '25PROBAR20'.
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
    """
    Upload and visualize Easy Growth sensor data.

    Methods
    -------
    GET:
      - Query params:
          sensor      -> matches Sensor.sensor_id (optional)
          start_date  -> YYYY-MM-DD (defaults to today - 14 days)
          end_date    -> YYYY-MM-DD (defaults to today)
      - If a sensor is selected, fetch SensorReading records within [start_date, end_date]
        ordered by timestamp, and build `chart_data` for the frontend chart.

    POST:
      - Accepts multiple JSON files under the "files" field (multipart/form-data).
      - For each file:
          * Infer sensor_id from the filename via parse_sensor_id_from_filename(...)
          * Load JSON and call process_json_data(data, sensor_id)
      - Shows per-file errors via Django messages; successful uploads get a summary message.

    Template context
    ----------------
      sensors           : QuerySet[Sensor] for the selector
      chart_data        : list[dict] with timestamp and sensor metrics for plotting
      latest_readings   : the last SensorReading in range (or None)
      default_start/end : ISO date strings used to prefill the date inputs

    Notes
    -----
    - Invalid dates trigger a user message and redirect (PRG pattern).
    - Consider renaming context key `latest_readings` -> `latest_reading` for consistency.
    """
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
        "chart_data_json": json.dumps(chart_data),
        "latest_readings": latest_reading,
        "default_start": default_start.isoformat(),
        "default_end": default_end.isoformat(),
    })
