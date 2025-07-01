from django.shortcuts import render
from .sd_card import detect_sd_cards
import os
import pandas as pd
from django.http import JsonResponse
from .models import Flight
from django.conf import settings
import csv
import datetime

def home_view(request):
    return render(request, 'mainapp/home.html')

def sd_card_view(request):
    sd_cards = detect_sd_cards()
    return render(request, 'mainapp/sd_card.html', {'sd_cards': sd_cards})

df = pd.read_csv("~/Downloads/Drone_Flying_Schedule_2025.csv")
print(df.columns)  # See what columns actually exist

def read_local_csv(request):
    # Replace <YourUsername> with your actual username or use os.path.expanduser
    downloads_path = os.path.expanduser("~/Downloads")
    csv_file_path = os.path.join(downloads_path, "Drone_Flying_Schedule_2025.csv")

    if not os.path.exists(csv_file_path):
        return JsonResponse({"error": f"CSV file not found at {csv_file_path}"}, status=404)

    try:
        df = pd.read_csv(csv_file_path)
        data = df.to_dict(orient="records")
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




def review_drone_flights(request):
    downloads_path = os.path.expanduser("~/Downloads")
    csv_file_path = os.path.join(downloads_path, "Drone_Flying_Schedule_2025.csv")

    flights = []
    fields = [{'value': 'all', 'label': 'All'}]
    flight_types = [{'value': 'all', 'label': 'All'}]
    drone_pilots = [{'value': 'all', 'label': 'All'}]

    # Get filters from GET request
    selected_field = request.GET.get('field', 'all')
    selected_flight_type = request.GET.get('flight_type', 'all')
    selected_drone_pilot = request.GET.get('drone_pilot', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if os.path.exists(csv_file_path):
        try:
            df = pd.read_csv(csv_file_path, sep=';')

            # Create renamed dataframe for ease
            df_renamed = pd.DataFrame()
            df_renamed['field'] = df['Flight Field ID']
            df_renamed['date'] = pd.to_datetime(df['Flight Date'])
            df_renamed['date_display'] = pd.to_datetime(df['Flight Date']).dt.strftime('%B %d, %Y')
            df_renamed['image_type'] = df['Route type (MS, 3D, Thermal, RGB)']
            df_renamed['drone_pilot'] = df['Drone Pilot']
            df_renamed['processing_status'] = df['P4D Processing']

            if 'Workable Data' in df.columns:
                df_renamed['coordinates_correct'] = df['Workable Data']
            else:
                df_renamed['coordinates_correct'] = ''

            # Filter the dataframe based on selections:
            if selected_field != 'all':
                df_renamed = df_renamed[df_renamed['field'] == selected_field]
            if selected_flight_type != 'all':
                df_renamed = df_renamed[df_renamed['image_type'] == selected_flight_type]
            if selected_drone_pilot != 'all':
                df_renamed = df_renamed[df_renamed['drone_pilot'] == selected_drone_pilot]
            if date_from:
                df_renamed = df_renamed[df_renamed['date'] >= pd.to_datetime(date_from)]
            if date_to:
                df_renamed = df_renamed[df_renamed['date'] <= pd.to_datetime(date_to)]

            flights = df_renamed.to_dict(orient='records')

            # Generate unique filter options dynamically:
            unique_fields = df['Flight Field ID'].dropna().unique()
            unique_flight_types = df['Route type (MS, 3D, Thermal, RGB)'].dropna().unique()
            unique_drone_pilots = df['Drone Pilot'].dropna().unique()

            fields += [{'value': f, 'label': f} for f in sorted(unique_fields)]
            flight_types += [{'value': f, 'label': f} for f in sorted(unique_flight_types)]
            drone_pilots += [{'value': p, 'label': p} for p in sorted(unique_drone_pilots)]

        except Exception as e:
            print(f"Error reading CSV: {e}")

    context = {
        'flights': flights,
        'fields': fields,
        'flight_types': flight_types,
        'drone_pilots': drone_pilots,
        # Pass selected filters to template for rendering selected options
        'selected_field': selected_field,
        'selected_flight_type': selected_flight_type,
        'selected_drone_pilot': selected_drone_pilot,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
    }

    return render(request, "mainapp/review_drone_flights.html", context)

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
    return os.path.exists(base_path)

def weekly_view(request, week_offset=0):
    week_offset = int(week_offset)

    csv_path = os.path.join(settings.BASE_DIR, 'mainapp', 'data', 'flight_list.csv')
    all_flights = []

    # Calculate the week's date range based on offset
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=week_offset)
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_num = start_of_week.isocalendar()[1]

    # Read and process CSV
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
        "end_date": end_of_week,
        "week_offset": week_offset
    }

    return render(request, "mainapp/weekly.html", context)
