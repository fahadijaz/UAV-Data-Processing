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

def folder_has_flight_in_week(base_path, start_date, end_date):
    if not os.path.isdir(base_path):
        return False

    for root, dirs, files in os.walk(base_path):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                mtime = datetime.date.fromtimestamp(os.path.getmtime(fp))
            except OSError:
                continue

            if start_date <= mtime <= end_date:
                return True

    return False


def weekly_view(request, week_offset=0):

    week_offset = int(week_offset)

    csv_path = os.path.join(settings.BASE_DIR, 'mainapp', 'data', 'flight_list.csv')
    all_flights = []

    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=week_offset)
    end_of_week   = start_of_week + datetime.timedelta(days=6)
    week_num      = start_of_week.isocalendar()[1]

    # Read the flight list CSV
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            field_name      = row["Field folder name"].strip()
            flight_type     = row["Type of flight"].strip()
            flown_path      = row["1_flight path"].strip()
            processed_path  = row["2_1_pix4d path"].strip()

            flown     = folder_has_flight_in_week(flown_path,     start_of_week, end_of_week)
            processed = folder_has_flight_in_week(processed_path, start_of_week, end_of_week)

            if not flown:
                status_level = 0  # red: no flight data
            elif not processed:
                status_level = 1  # orange: flight flown but not processed
            else:
                status_level = 2  # green: flown & processed

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