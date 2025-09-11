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
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
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
   if not dcim_path:
       raise ValueError("DCIM path cannot be None or empty")
   
   dcim_path = Path(dcim_path)
   if not dcim_path.exists() or not dcim_path.is_dir():
       raise ValueError(f"DCIM path does not exist or is not a directory: {dcim_path}")
   
   for name in os.listdir(dcim_path):
       p = dcim_path / name
       if not p.is_dir():
           continue
       m = FOLDER_RE.match(name)
       if m:
           yield p, m.group("flight_path")

def build_initial_flights(dcim_path):
   if not dcim_path:
       logger.warning("No DCIM path provided")
       return []
   
   initial = []
   try:
       for path, key in discover_flights(dcim_path):
           initial.append({
               "flight_path_key": key,
               "flight_dir": str(path),
               "folder_name": path.name,
               "skyline_names": "",
           })
       logger.debug("Found %d flight directories", len(initial))
       return initial
   except (ValueError, OSError) as e:
       logger.error("Error building initial flights: %s", e)
       return []

def _match_flight_path(key: str):
    key_core = _core_key(_normalize_name(key))
    for fp in Flight_Paths.objects.all():
        db_core = _core_key(_normalize_name(fp.flight_path_name))
        if db_core == key_core:
            return fp
    return None

def _normalize_name(s: str) -> list[str]:
    s = (s or "").lower().strip()
    s = s.replace(".kmz", "")
    s = s.replace("horizontal", "oblique").replace("vertical", "oblique")
    s = s.replace("_", "-")
    parts = [p for p in s.split("-") if p]
    return parts

def _core_key(parts: list[str]) -> str:
    idx = None
    for i, p in enumerate(parts):
        if p.endswith("m") and p[:-1].isdigit():
            idx = i
    if idx is None:
        return "-".join(parts)
    core = parts[:idx + 1]
    return "-".join(core)

def copy_flight_with_reflectance(source_dir, dest_base, reflectance_dir, logger):
    source_path = Path(source_dir)
    dest_path = Path(dest_base)

    dest_path.mkdir(parents=True, exist_ok=True)
    
    main_dest = dest_path / source_path.name
    logger.info("Copying main flight folder: %s -> %s", source_path, main_dest)
    shutil.copytree(source_dir, main_dest, dirs_exist_ok=True)
    
    reflectance_copied = False
    if reflectance_dir and reflectance_dir.strip():
        reflectance_path = Path(reflectance_dir.strip())
        if reflectance_path.exists() and reflectance_path.is_dir():
            reflectance_dest = dest_path / reflectance_path.name
            
            try:
                logger.info("Copying reflectance panel: %s -> %s", reflectance_path, reflectance_dest)
                shutil.copytree(reflectance_path, reflectance_dest, dirs_exist_ok=True)
                reflectance_copied = True
                logger.info("Successfully copied reflectance panel folder")
            except Exception as e:
                logger.error("Failed to copy reflectance panel %s: %s", reflectance_path, e)
        else:
            logger.warning("Reflectance panel directory not found or not a directory: %s", reflectance_dir)
    
    return reflectance_copied

def _match_flight_path(key: str):
    key_core = _core_key(_normalize_name(key))
    for fp in Flight_Paths.objects.all():
        db_core = _core_key(_normalize_name(fp.flight_path_name))
        if db_core == key_core:
            return fp
    return None

def _normalize_name(s: str) -> list[str]:
    s = (s or "").lower().strip()
    s = s.replace(".kmz", "")
    s = s.replace("horizontal", "oblique").replace("vertical", "oblique")
    s = s.replace("_", "-")
    parts = [p for p in s.split("-") if p]
    return parts

def _core_key(parts: list[str]) -> str:
    idx = None
    for i, p in enumerate(parts):
        if p.endswith("m") and p[:-1].isdigit():
            idx = i
    if idx is None:
        return "-".join(parts)
    core = parts[:idx + 1]
    return "-".join(core)

def copy_flight_with_reflectance(source_dir, dest_base, reflectance_dir, logger):
    source_path = Path(source_dir)
    dest_path = Path(dest_base)

    dest_path.mkdir(parents=True, exist_ok=True)
    
    main_dest = dest_path / source_path.name
    logger.info("Copying main flight folder: %s -> %s", source_path, main_dest)
    shutil.copytree(source_dir, main_dest, dirs_exist_ok=True)
    
    reflectance_copied = False
    if reflectance_dir and reflectance_dir.strip():
        reflectance_path = Path(reflectance_dir.strip())
        if reflectance_path.exists() and reflectance_path.is_dir():
            reflectance_dest = dest_path / reflectance_path.name
            
            try:
                logger.info("Copying reflectance panel: %s -> %s", reflectance_path, reflectance_dest)
                shutil.copytree(reflectance_path, reflectance_dest, dirs_exist_ok=True)
                reflectance_copied = True
                logger.info("Successfully copied reflectance panel folder")
            except Exception as e:
                logger.error("Failed to copy reflectance panel %s: %s", reflectance_path, e)
        else:
            logger.warning("Reflectance panel directory not found or not a directory: %s", reflectance_dir)
    
    return reflectance_copied

def _match_flight_path(key: str):
    key_core = _core_key(_normalize_name(key))
    for fp in Flight_Paths.objects.all():
        db_core = _core_key(_normalize_name(fp.flight_path_name))
        if db_core == key_core:
            return fp
    return None

def _normalize_name(s: str) -> list[str]:
    s = (s or "").lower().strip()
    s = s.replace(".kmz", "")
    s = s.replace("horizontal", "oblique").replace("vertical", "oblique")
    s = s.replace("_", "-")
    parts = [p for p in s.split("-") if p]
    return parts

def _core_key(parts: list[str]) -> str:
    idx = None
    for i, p in enumerate(parts):
        if p.endswith("m") and p[:-1].isdigit():
            idx = i
    if idx is None:
        return "-".join(parts)
    core = parts[:idx + 1]
    return "-".join(core)

def copy_flight_with_reflectance(source_dir, dest_base, reflectance_dir, logger):
    source_path = Path(source_dir)
    dest_path = Path(dest_base)

    dest_path.mkdir(parents=True, exist_ok=True)
    
    main_dest = dest_path / source_path.name
    logger.info("Copying main flight folder: %s -> %s", source_path, main_dest)
    shutil.copytree(source_dir, main_dest, dirs_exist_ok=True)
    
    reflectance_copied = False
    if reflectance_dir and reflectance_dir.strip():
        reflectance_path = Path(reflectance_dir.strip())
        if reflectance_path.exists() and reflectance_path.is_dir():
            reflectance_dest = dest_path / reflectance_path.name
            
            try:
                logger.info("Copying reflectance panel: %s -> %s", reflectance_path, reflectance_dest)
                shutil.copytree(reflectance_path, reflectance_dest, dirs_exist_ok=True)
                reflectance_copied = True
                logger.info("Successfully copied reflectance panel folder")
            except Exception as e:
                logger.error("Failed to copy reflectance panel %s: %s", reflectance_path, e)
        else:
            logger.warning("Reflectance panel directory not found or not a directory: %s", reflectance_dir)
    
    return reflectance_copied

def _match_flight_path(key: str):
    key_core = _core_key(_normalize_name(key))
    for fp in Flight_Paths.objects.all():
        db_core = _core_key(_normalize_name(fp.flight_path_name))
        if db_core == key_core:
            return fp
    return None

def _normalize_name(s: str) -> list[str]:
    s = (s or "").lower().strip()
    s = s.replace(".kmz", "")
    s = s.replace("horizontal", "oblique").replace("vertical", "oblique")
    s = s.replace("_", "-")
    parts = [p for p in s.split("-") if p]
    return parts

def _core_key(parts: list[str]) -> str:
    idx = None
    for i, p in enumerate(parts):
        if p.endswith("m") and p[:-1].isdigit():
            idx = i
    if idx is None:
        return "-".join(parts)
    core = parts[:idx + 1]
    return "-".join(core)

def copy_flight_with_reflectance(source_dir, dest_base, reflectance_dir, logger):
    source_path = Path(source_dir)
    dest_path = Path(dest_base)

    dest_path.mkdir(parents=True, exist_ok=True)
    
    main_dest = dest_path / source_path.name
    logger.info("Copying main flight folder: %s -> %s", source_path, main_dest)
    shutil.copytree(source_dir, main_dest, dirs_exist_ok=True)
    
    reflectance_copied = False
    if reflectance_dir and reflectance_dir.strip():
        reflectance_path = Path(reflectance_dir.strip())
        if reflectance_path.exists() and reflectance_path.is_dir():
            reflectance_dest = dest_path / reflectance_path.name
            
            try:
                logger.info("Copying reflectance panel: %s -> %s", reflectance_path, reflectance_dest)
                shutil.copytree(reflectance_path, reflectance_dest, dirs_exist_ok=True)
                reflectance_copied = True
                logger.info("Successfully copied reflectance panel folder")
            except Exception as e:
                logger.error("Failed to copy reflectance panel %s: %s", reflectance_path, e)
        else:
            logger.warning("Reflectance panel directory not found or not a directory: %s", reflectance_dir)
    
    return reflectance_copied

def process_flights_post(formset, selected_dcim, request):
    if not formset.is_valid():
        logger.warning("Formset invalid: %s", formset.errors)
        return None

    processed = 0
    logger.debug("Starting processing of %d forms", len(formset.forms))

    for i, form in enumerate(formset.forms, start=1):
        cd = form.cleaned_data
        logger.debug("Form %d cleaned_data: %s", i, cd)
        key = cd.get("flight_path_key")
        if not key:
            logger.warning("Form %d has no flight_path_key, skipping", i)
            continue

        fp = _match_flight_path(key)
        folder_name = Path(cd["flight_dir"]).name
        reflectance_dir = cd.get("reflectance_dir", "")
        logger.debug("Form %d folder_name: %s, reflectance_dir: %s", i, folder_name, reflectance_dir)

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
        logger.debug("Form %d date_str: %s", i, date_str)

        if fp:
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
            logger.info("Matched DB config for %s", key)
        else:
            new_folder = f"{date_str} {folder_name}"
            base = Path(selected_dcim).parent
            logger.warning("No DB config for %s, copying raw folder", key)

        dest = base / new_folder
        logger.debug("Form %d copying from %s -> %s", i, cd["flight_dir"], dest)
        
        try:
            reflectance_copied = copy_flight_with_reflectance(
                cd["flight_dir"], dest, reflectance_dir, logger
            )
            logger.info("Copied flight %s (reflectance panel: %s)", 
                       new_folder, "Yes" if reflectance_copied else "No")
            
        except Exception as e:
            logger.error("Error copying %s -> %s: %s", cd["flight_dir"], dest, e)
            messages.error(request, f"Failed to copy {folder_name}: {e}")
            continue

        skyline_names = cd.get("skyline_names", "").strip()
        if skyline_names:
            try:
                process_skyline_images(cd["flight_dir"], dest, skyline_names, logger)
                logger.info("Processed skyline images for %s", new_folder)
            except Exception as e:
                logger.error("Error processing skyline images for %s: %s", new_folder, e)
                messages.warning(request, f"Skyline processing failed for {new_folder}: {e}")

        if fp:
            ws = ",".join(str(cd.get(f"wind_speed{i}") or 0) for i in (1, 2, 3))
            Flight_Log.objects.create(
                foldername        = new_folder,
                flight_field_id   = key,
                project           = fp.project,
                flight_type       = fp.type_of_flight,
                drone_type        = cd.get("drone_model"),
                drone_pilot       = cd.get("pilot"),
                reflectance_panel = "Yes" if reflectance_copied else "No",
                flight_date       = datetime.strptime(date_str, "%Y%m%d").date(),
                flight_comments   = cd.get("comments", "") + 
                                  (" [Reflectance panel included]" if reflectance_copied else ""),
                flight_wind_speed = ws,
                flight_height     = height,
                flight_side_over  = str(int(fp.side_overlap)) if fp.side_overlap else "",
                flight_front_over = str(int(fp.front_overlap)) if fp.front_overlap else "",
                new_folder_name   = new_folder,
                root_folder       = str(fp.first_flight_path),
                flight_path       = fp.flight_path_name,
                p4d_path          = fp.pix4d_path,
            )
            logger.info("Created Flight_Log for %s (reflectance: %s)", 
                       new_folder, "Yes" if reflectance_copied else "No")
        else:
            logger.warning("No Flight_Paths match for %s, skipping Flight_Log creation", key)

        processed += 1

    logger.debug("Finished processing. Total processed: %d", processed)
    return processed

def process_skyline_images(source_dir, dest_dir, skyline_names, logger):
    if not skyline_names.strip():
        logger.debug("No skyline files specified")
        return
    
    skyline_dest_base = dest_dir.parent.parent / "_SKYLINE"
    skyline_dest = skyline_dest_base / dest_dir.name
    
    logger.info("Creating skyline directory: %s", skyline_dest)
    skyline_dest.mkdir(parents=True, exist_ok=True)
    
    source_path = Path(source_dir)
    skyline_flight_dest = skyline_dest / source_path.name
    
    try:
        logger.info("Copying entire flight folder for skyline: %s -> %s", source_path, skyline_flight_dest)
        shutil.copytree(source_path, skyline_flight_dest, dirs_exist_ok=True)
        logger.info("Successfully copied entire flight folder to skyline location")
    except Exception as e:
        logger.error("Failed to copy flight folder to skyline: %s", e)

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