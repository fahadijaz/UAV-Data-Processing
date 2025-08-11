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
        return find_sd_cards_windows(dcim_folder)
    return find_sd_cards_unix(dcim_folder)


if __name__ == "__main__":
    BASE_OUTPUT = r"E:\PheNo"
    os.makedirs(BASE_OUTPUT, exist_ok=True)

    for dcim_path in detect_sd_cards():
        print(f"Found DCIM folder at:\n  {dcim_path}\n")
        # Move each subfolder (e.g. "100MEDIA", "101MEDIA", "DJI_…") out of DCIM:
        for sub in os.listdir(dcim_path):
            src_folder = os.path.join(dcim_path, sub)
            if not os.path.isdir(src_folder):
                continue

            dest = os.path.join(BASE_OUTPUT, sub)
            print(f"Moving:\n  {src_folder}\n→ {dest}\n")
            shutil.move(src_folder, dest)
