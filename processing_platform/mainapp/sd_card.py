import os
import platform
import re
import string
import ctypes
import shutil
import logging
from pathlib import Path
from datetime import datetime, date
from django import forms
from django.forms import formset_factory
from django.contrib import messages
from .forms import FlightForm
from .models import Flight_Paths, Flight_Log

logger = logging.getLogger("mainapp")

FOLDER_RE = re.compile(r'''
    ^
    (?:DJI_(?P<timestamp>\d{12})_[0-9]{3}_)?
    (?P<flight_path>\d+-[\w-]+-\d+m-[\w-]+(?:-\d+){0,2})
    $
''', re.VERBOSE)

FlightFormSet = formset_factory(FlightForm, extra=0)

class SDCardError(Exception):
    pass

def is_removable_drive_windows(drive_letter):
    DRIVE_REMOVABLE = 2
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive_letter}:/")
    return drive_type == DRIVE_REMOVABLE

def find_sd_cards_windows(dcim_folder="DCIM"):
    sd_cards = []
    for drive_letter in string.ascii_uppercase:
        drive = f"{drive_letter}:/"
        candidate = os.path.join(drive, dcim_folder)
        if is_removable_drive_windows(drive_letter) and os.path.isdir(candidate):
            sd_cards.append(candidate)
    return sd_cards

def find_sd_cards_unix(dcim_folder="DCIM"):
    sd_cards = []
    for base in ("/media", "/Volumes", "/mnt"):
        if not os.path.isdir(base):
            continue
        for dev in os.listdir(base):
            candidate = os.path.join(base, dev, dcim_folder)
            if os.path.isdir(candidate):
                sd_cards.append(candidate)
    return sd_cards

def detect_sd_cards(dcim_folder="DCIM"):
    if platform.system() == "Windows":
        cards = find_sd_cards_windows(dcim_folder)
    else:
        cards = find_sd_cards_unix(dcim_folder)
    if not cards:
        raise SDCardError("No SD cards detected.")
    return cards

def discover_flights(dcim_path):
    for name in os.listdir(dcim_path):
        p = Path(dcim_path) / name
        if not p.is_dir():
            continue
        m = FOLDER_RE.match(name)
        if m:
            yield p, m.group("flight_path")

def build_initial_flights(dcim_path):
    initial = []
    for path, key in discover_flights(dcim_path):
        initial.append({
            "flight_path_key": key,
            "flight_dir": str(path),
            "folder_name": path.name,
            "skyline_names": "",
        })
    logger.debug("Found %d flight directories", len(initial))
    return initial

def process_flights_post(formset, selected_dcim, request):
    if not formset.is_valid() or "upload" not in request.POST:
        logger.warning(
            "Formset invalid or no upload: %s | upload? %s",
            formset.errors, "upload" in request.POST
        )
        return None
    processed = 0
    for form in formset:
        cd = form.cleaned_data
        key = cd.get("flight_path_key")
        try:
            fp = Flight_Paths.objects.get(
                flight_path_name__startswith=key
            )
        except Flight_Paths.DoesNotExist:
            messages.warning(request, f"No config for flight {key}")
            continue
        folder_name = Path(cd["flight_dir"]).name
        m = FOLDER_RE.match(folder_name)
        if m and m.group("timestamp"):
            ts = m.group("timestamp")[:8]
            try:
                datetime.strptime(ts, "%Y%m%d")
                date_str = ts
            except ValueError:
                date_str = date.today().strftime("%Y%m%d")
        else:
            date_str = date.today().strftime("%Y%m%d")
        height = f"{int(fp.flight_height)}m" if fp.flight_height else ""
        overlap = ""
        if fp.side_overlap is not None and fp.front_overlap is not None:
            overlap = f"{int(fp.side_overlap)} {int(fp.front_overlap)}"
        parts = [
            date_str,
            fp.short_id,
            cd.get("drone_model", ""),
            height,
            fp.type_of_flight,
            overlap,
        ]
        new_folder = " ".join(p for p in parts if p)
        base = Path(fp.first_flight_path)
        dest = base / new_folder
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(cd["flight_dir"], dest, dirs_exist_ok=True)
        ref_dir = cd.get("reflectance_dir")
        if ref_dir:
            ref_src = Path(ref_dir)
            if ref_src.is_dir():
                shutil.copytree(
                    str(ref_src),
                    str(dest / ref_src.name),
                    dirs_exist_ok=True
                )
        uploads = request.FILES.getlist(f"{form.prefix}-skyline_files") if hasattr(request.FILES, "getlist") else ([request.FILES[f"{form.prefix}-skyline_files"]] if f"{form.prefix}-skyline_files" in request.FILES else [])
        tmp = dest / "_tmp"
        skyline = (
            cd.get("skyline_names", "").split(",")
            if cd.get("skyline_names")
            else []
        )
        if uploads:
            tmp.mkdir(exist_ok=True)
            for uf in uploads:
                with (tmp / uf.name).open("wb+") as f:
                    for chunk in uf.chunks():
                        f.write(chunk)
                skyline.append(uf.name)
        if skyline:
            sky_root = base.parent[2] / "_SKYLINE" / new_folder
            sky_root.mkdir(parents=True, exist_ok=True)
            for name in skyline:
                src = tmp / name if (tmp / name).exists() else dest / name
                if src.exists():
                    shutil.move(str(src), str(sky_root / name))
            if tmp.exists():
                shutil.rmtree(tmp)
        ws = ",".join(str(cd.get(f"wind_speed{i}")) for i in (1, 2, 3))
        Flight_Log.objects.create(
            foldername        = new_folder,
            flight_field_id   = key,
            project           = fp.project,
            flight_type       = fp.type_of_flight,
            drone_type        = cd.get("drone_model"),
            drone_pilot       = cd.get("pilot"),
            reflectance_panel = "Yes" if ref_dir else "No",
            flight_date       = datetime.strptime(date_str, "%Y%m%d").date(),
            flight_comments   = cd.get("comments", ""),
            flight_wind_speed = ws,
            flight_height     = height,
            flight_side_over  = str(int(fp.side_overlap)) if fp.side_overlap else "",
            flight_front_over = str(int(fp.front_overlap)) if fp.front_overlap else "",
            new_folder_name   = new_folder,
            root_folder       = str(fp.first_flight_path),
            flight_path       = fp.flight_path_name,
            p4d_path          = fp.pix4d_path,
        )
        processed += 1
    return processed
