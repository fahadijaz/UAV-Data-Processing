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
        candidate = os.path.join(drive_path, dcim_folder)
        try:
            if is_removable_drive_windows(drive_letter) and os.path.isdir(candidate):
                sd_cards.append(candidate)
        except Exception:
            pass
    return sd_cards

def find_sd_cards_unix(dcim_folder="DCIM"):
    base_dirs = ["/media", "/Volumes", "/mnt"]
    sd_cards = []
    for base_path in base_dirs:
        if os.path.isdir(base_path):
            for device in os.listdir(base_path):
                candidate = os.path.join(base_path, device, dcim_folder)
                if os.path.isdir(candidate):
                    sd_cards.append(candidate)
    return sd_cards

def detect_sd_cards(dcim_folder="DCIM"):
    if platform.system() == "Windows":
        return find_sd_cards_windows(dcim_folder)
    else:
        return find_sd_cards_unix(dcim_folder)

# placeholder for your DJI filename parser (unused for now)
def parse_dji_filename(filename):
    base_output = r"E:\PheNo"
    sensor = "M4T"
    orient_map = {"Oblique": "3D"}

    name, ext = os.path.splitext(filename)
    parts = name.split('_')
    if len(parts) != 4:
        raise ValueError(f"Bad DJI pattern: {filename}")

    date = parts[1][:8]
    flight_i, project, alt, orient_raw, ang_min, ang_max = parts[3].split('-')
    orient = orient_map.get(orient_raw, orient_raw)

    folder_name = f"{date} {project} {sensor} {alt} {orient} {ang_min} {ang_max}"
    return os.path.join(base_output, project, orient, folder_name)

if __name__ == "__main__":
    # hard-coded destination root
    BASE_OUTPUT = r"E:\PheNo"
    os.makedirs(BASE_OUTPUT, exist_ok=True)

    for dcim_path in detect_sd_cards():
        print(f"Found DCIM at: {dcim_path}")
        # move each immediate subfolder (e.g. DJI folders like 100MEDIA) out of DCIM
        for sub in os.listdir(dcim_path):
            src_folder = os.path.join(dcim_path, sub)
            if not os.path.isdir(src_folder):
                continue
            dest_folder = os.path.join(BASE_OUTPUT, sub)
            print(f"Moving:\n  {src_folder}\n→ {dest_folder}\n")
            shutil.move(src_folder, dest_folder)
