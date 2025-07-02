from django.shortcuts import render
from .sd_card import detect_sd_cards
import os
import pandas as pd
from django.http import JsonResponse

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
