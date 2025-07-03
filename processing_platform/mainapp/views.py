from django.shortcuts import render, redirect
from .sd_card import detect_sd_cards
from .models import Flight
from django.conf import settings
import os
import csv
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminUserCreationForm

User = get_user_model()

def superuser_required(view_func):
    return login_required(
        user_passes_test(lambda u: u.is_superuser, login_url='login')(view_func)
    )

@superuser_required
def admin_panel(request):
    users = User.objects.all().order_by('username')

    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_panel')
    else:
        form = AdminUserCreationForm()

    return render(request, 'admin/admin_panel.html', {
        'users': users,
        'form': form,
    })


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

def parse_date_from_foldername(foldername):
    parts = foldername.split('_')
    if len(parts) < 2:
        raise ValueError(f"Unexpected foldername format: {foldername}")
    
    ts = parts[1]
    if len(ts) < 8:
        raise ValueError(f"Timestamp too short in foldername: {foldername}")
    
    date_part = ts[:8]
    return datetime.datetime.strptime(date_part, "%Y%m%d").date()


def extract_project_field_type(flight_path):
    try:
        parts = flight_path.replace('\\', '/').split('/')
        if len(parts) >= 4:
            project = parts[-4] if '1_flights' in parts else None
            field = parts[-2] if len(parts) >= 2 else None
            flight_type = parts[-1] if parts[-1] else (parts[-2] if len(parts) >= 2 else None)
            return project, field, flight_type
    except:
        pass
    
    return None, None, None


def weekly_view(request, week_offset=0):
    week_offset = int(week_offset)
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(weeks=week_offset)
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_num = start_of_week.isocalendar()[1]
    
    log_csv = os.path.join(settings.BASE_DIR, 'mainapp', 'data', 'Flight_log.csv')
    schedule_csv = os.path.join(settings.BASE_DIR, 'mainapp', 'data', 'flight_list.csv')
    
    flown_flights = set()
    processed_flights = set()
    
    try:
        with open(log_csv, newline='', encoding='utf-8') as logfile:
            reader = csv.DictReader(logfile, delimiter=';')
            for row in reader:
                foldername = row.get("Foldername", "").strip()
                if not foldername:
                    continue
                
                try:
                    flight_date = parse_date_from_foldername(foldername)
                except Exception as e:
                    print(f"Could not parse date from {foldername}: {e}")
                    continue
                
                if not (start_of_week <= flight_date <= end_of_week):
                    continue
                
                raw_folder = row.get("Flight path", "").strip()
                pix4d_folder = row.get("Pix4D path", "").strip()
                
                if raw_folder:
                    project, field, flight_type = extract_project_field_type(raw_folder)
                    if project and field and flight_type:
                        flight_key = (project, field, flight_type)
                        flown_flights.add(flight_key)
                        
                        if pix4d_folder and os.path.isdir(pix4d_folder):
                            processed_flights.add(flight_key)
    
    except FileNotFoundError:
        print(f"Flight_log.csv not found at {log_csv}")
        flown_flights = set()
        processed_flights = set()
    except Exception as e:
        print(f"Error reading Flight_log.csv: {e}")
        flown_flights = set()
        processed_flights = set()
    
    all_flights = []
    try:
        with open(schedule_csv, newline='', encoding='utf-8') as schedfile:
            reader = csv.DictReader(schedfile, delimiter=';')
            for row in reader:
                field_name = row.get("Field folder name", "").strip()
                flight_type = row.get("Type of flight", "").strip()
                project_name = row.get("Project", "").strip()
                frequency = row.get("Frequency", "").strip()
                
                if not field_name or not flight_type or not project_name:
                    continue
                
                flight_key = (project_name, field_name, flight_type)
                
                flown = flight_key in flown_flights
                processed = flight_key in processed_flights
                
                if not flown:
                    status_level = 0
                elif not processed:
                    status_level = 1
                else:
                    status_level = 2
                
                all_flights.append({
                    "project": project_name,
                    "field": field_name,
                    "type": flight_type,
                    "frequency": frequency,
                    "flown": flown,
                    "processed": processed,
                    "status_level": status_level,
                })
    
    except FileNotFoundError:
        print(f"flight_list.csv not found at {schedule_csv}")
    except Exception as e:
        print(f"Error reading flight_list.csv: {e}")
    
    all_flights.sort(key=lambda x: x["status_level"])
    
    return render(request, "mainapp/weekly.html", {
        "flights": all_flights,
        "week_num": week_num,
        "start_date": start_of_week,
        "end_date": end_of_week,
        "week_offset": week_offset,
        "total_flights": len(all_flights),
        "flown_count": len([f for f in all_flights if f["flown"]]),
        "processed_count": len([f for f in all_flights if f["processed"]]),
    })
