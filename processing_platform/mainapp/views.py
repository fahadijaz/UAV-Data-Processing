from django.shortcuts import render
from .sd_card import detect_sd_cards
from .models import Flight
from django.conf import settings
import os
import csv
import datetime


def home_view(request):
    return render(request, 'mainapp/home.html')

def sd_card_view(request):
    sd_cards = detect_sd_cards()
    return render(request, 'mainapp/sd_card.html', {'sd_cards': sd_cards})

def details_view(request):
    return render(request, 'mainapp/details.html')

def add_routes_view(request):
    return render(request, 'mainapp/add_routes.html')

def flight_events(request):
    events = []
    for flight in Flight.objects.all():
        color = "#00cc66" if flight.flown else "#ff6666"  # green if flown, red if not
        title = f"{flight.title} - {flight.pilot.name if flight.pilot else 'Unassigned'}"

        events.append({
            "title": title,
            "start": flight.scheduled_time.isoformat(),
            "end": flight.end_time.isoformat(),
            "color": color,
            "extendedProps": {
                "flown": flight.flown,
                "pilot": flight.pilot.name if flight.pilot else None,
                "frequency_days": flight.frequency_days,
            }
        })
    return JsonResponse(events, safe=False)

def parse_date(datestr):
    return datetime.datetime.strptime(datestr, "%d-%b-%Y").date()

def weekly_view(request, week_offset=0):
    week_offset = int(week_offset)

    today         = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) \
                    + datetime.timedelta(weeks=week_offset)
    end_of_week   = start_of_week + datetime.timedelta(days=6)
    week_num      = start_of_week.isocalendar()[1]

    log_csv = os.path.join(settings.BASE_DIR,'mainapp', 'data', 'Flight_log.csv')

    flown_folders    = set()
    processed_folders = set()

    with open(log_csv, newline='') as logfile:
        reader = csv.DictReader(logfile, delimiter=';')
        for row in reader:
            try:
                flight_date = parse_date(row["Flight Date"].strip())
            except (ValueError, KeyError):
                continue

            if not (start_of_week <= flight_date <= end_of_week):
                continue

            raw_folder   = row["Flight path"].strip()
            pix4d_folder = row["Pix4D path"].strip()

            if os.path.isdir(raw_folder):
                flown_folders.add(raw_folder)
            if os.path.isdir(pix4d_folder):
                processed_folders.add(pix4d_folder)

    schedule_csv = os.path.join(settings.BASE_DIR,'mainapp', 'data', 'flight_list.csv')

    all_flights = []
    with open(schedule_csv, newline='') as schedfile:
        reader = csv.DictReader(schedfile, delimiter=';')
        for row in reader:
            field_name     = row["Field folder name"].strip()
            flight_type    = row["Type of flight"].strip()
            flown_path     = row["1_flight path"].strip()
            processed_path = row["2_1_pix4d path"].strip()

            flown     = (flown_path    in flown_folders)
            processed = (processed_path in processed_folders)

            if not flown:
                status_level = 0   # red
            elif not processed:
                status_level = 1   # orange
            else:
                status_level = 2   # green

            all_flights.append({
                "field":        field_name,
                "type":         flight_type,
                "flown":        flown,
                "processed":    processed,
                "status_level": status_level,
            })

    all_flights.sort(key=lambda x: x["status_level"])

    context = {
        "flights":     all_flights,
        "week_num":    week_num,
        "start_date":  start_of_week,
        "end_date":    end_of_week,
        "week_offset": week_offset,
    }
    return render(request, "mainapp/weekly.html", context)
