import os
import platform
import string
import ctypes

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
