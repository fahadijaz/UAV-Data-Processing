import os
import platform
import string
import ctypes
import shutil

def is_removable_drive_windows(drive_letter):
    DRIVE_REMOVABLE = 2
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive_letter}:/")
    return drive_type == DRIVE_REMOVABLE

def find_sd_cards_windows(dcim_folder="DCIM"):
    sd_cards = []
    for drive_letter in string.ascii_uppercase:
        drive_path = f"{drive_letter}:/"
        target_path = os.path.join(drive_path, dcim_folder)
        try:
            if is_removable_drive_windows(drive_letter) and os.path.exists(target_path):
                sd_cards.append(target_path)
        except Exception:
            pass
    return sd_cards

def find_sd_cards_unix(dcim_folder="DCIM"):
    base_dirs = ["/media", "/Volumes", "/mnt"]
    sd_cards = []
    for base_path in base_dirs:
        if os.path.exists(base_path):
            for device in os.listdir(base_path):
                device_path = os.path.join(base_path, device)
                target_path = os.path.join(device_path, dcim_folder)
                if os.path.isdir(target_path):
                    sd_cards.append(target_path)
    return sd_cards

def detect_sd_cards(dcim_folder="DCIM"):
    system = platform.system()
    if system == "Windows":
        return find_sd_cards_windows(dcim_folder)
    else:
        return find_sd_cards_unix(dcim_folder)

def parse_dji_filename(filename):
    """
    From 'DJI_202507061335_002_25-RobOat-20m-Oblique-80-85.ext'
    → 'P:\\PheNo\\RobOat\\1_flights\\RobOat\\3D\\20250706 RobOat M4T 20m 3D 80 85'
    """
    base_output = r"E:\PheNo"
    sensor = "M4T"                              # sensor label
    orient_map = {"Oblique": "3D"}             

    name, ext = os.path.splitext(filename)
    parts = name.split('_')
    if len(parts) != 4:
        raise ValueError(f"Bad DJI pattern: {filename}")

    date = parts[1][:8]                         # "20250706"
    flight_i, project, alt, orient_raw, ang_min, ang_max = parts[3].split('-')
    orient = orient_map.get(orient_raw, orient_raw)

    folder_name = f"{date} {project} {sensor} {alt} {orient} {ang_min} {ang_max}"
    return os.path.join(base_output, project, orient, folder_name)

if __name__ == "__main__":
    for dcim_path in detect_sd_cards():
        print(f"Scanning SD card at {dcim_path}…")
        for root, dirs, files in os.walk(dcim_path):
            for f in files:
                if not f.startswith("DJI_"):
                    continue
                src = os.path.join(root, f)
                try:
                    dest_folder = parse_dji_filename(f)
                except ValueError as e:
                    print(f"Skipping {f}: {e}")
                    continue

                # ensure the folder exists
                os.makedirs(dest_folder, exist_ok=True)

                # move the file
                dest = os.path.join(dest_folder, f)
                print(f"Moving:\n  {src}\n→ {dest}\n")
                shutil.move(src, dest)
