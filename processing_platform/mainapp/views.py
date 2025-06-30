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
    csv_path = os.path.join(settings.BASE_DIR, 'mainapp', 'data', 'flight_list.csv')
    all_flights = []

    # Get current week range
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_num = today.isocalendar()[1]

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            field_name = row["Field folder name"].strip()
            flight_type = row["Type of flight"].strip()

            flown_path = row["1_flight path"].strip()
            processed_path = row["2_1_pix4d path"].strip()

            flown = folder_exists_for_week(flown_path, start_of_week, end_of_week)
            processed = folder_exists_for_week(processed_path, start_of_week, end_of_week)

            if not flown:
                status_level = 0  # red
            elif not processed:
                status_level = 1  # orange
            else:
                status_level = 2  # green

            all_flights.append({
                "field": field_name,
                "type": flight_type,
                "flown": flown,
                "processed": processed,
                "status_level": status_level
            })

    all_flights.sort(key=lambda x: x["status_level"])

    context = {
        "flights": all_flights,
        "week_num": week_num,
        "start_date": start_of_week,
        "end_date": end_of_week
    }

    return render(request, "mainapp/weekly.html", context)

