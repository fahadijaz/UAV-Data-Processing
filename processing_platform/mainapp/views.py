import csv
import datetime
import os

import pandas as pd
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.contrib import messages

from .models import Flight, Flight_Log
from .sd_card import detect_sd_cards, parse_dji_filename


def home_view(request):
    return render(request, "mainapp/home.html")


logger = logging.getLogger(__name__)

def sd_card_view(request):
    sd_cards = detect_sd_cards()
    logger.debug("sd_cards = %r", sd_cards)

    if request.method == "POST":
        sd_card_dcim = request.POST.get("sd_card")
        logger.debug("User picked SD card: %r", sd_card_dcim)

        moved = 0
        for root, dirs, files in os.walk(sd_card_dcim):
            logger.debug("Walking %r, %d files", root, len(files))
            for fname in files:
                if not fname.startswith("DJI_"):
                    continue
                src = os.path.join(root, fname)
                logger.debug(" → considering %r", src)

                try:
                    dest_folder = parse_dji_filename(fname)
                except Exception as e:
                    logger.warning("   parse failed for %r: %s", fname, e)
                    continue

                dest = os.path.join(dest_folder, fname)
                logger.debug("   will move to %r", dest)

                try:
                    os.makedirs(dest_folder, exist_ok=True)
                    shutil.move(src, dest)
                    moved += 1
                except Exception as e:
                    logger.error("   move error %r → %r: %s", src, dest, e)

        logger.info("Total moved: %d", moved)
        messages.success(request, f"Moved {moved} files from {sd_card_dcim}.")
        return redirect("sd_card")

    return render(request, "mainapp/sd_card.html", { "sd_cards": sd_cards })


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
