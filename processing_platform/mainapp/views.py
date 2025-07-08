import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

import csv
import os
import re
import pandas as pd
import shutil

# Date/time imports
from datetime import date, datetime

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.contrib import messages

from .models import Flight_Log, Flight_Paths
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


def sd_card_view(request):
    print(">>> ENTER sd_card_view, method:", request.method)
    logger.debug("⇒ Enter sd_card_view; method=%s", request.method)

    sd_cards = detect_sd_cards()
    print(">>> detect_sd_cards returned:", sd_cards)
    logger.debug("Detected SD cards: %r", sd_cards)

    drone_models = (
        Flight_Paths.objects
        .order_by()
        .values_list('drone_model', flat=True)
        .distinct()
    )
    print(">>> available drone_models:", list(drone_models))
    logger.debug("Available drone models: %r", list(drone_models))

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
            new_folder = f"{today_str}_{fp.short_id}_{selected_drone}_{fp.type_of_flight}_{side};{front}"
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
