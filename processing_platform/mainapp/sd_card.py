import os
import platform
import string
import ctypes
import csv
import re
import shutil
from pathlib import Path


def is_removable_drive_windows(letter):
    return ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:/") == 2

def find_sd_cards_windows(dcim="DCIM"):
    cards = []
    for l in string.ascii_uppercase:
        p = f"{l}:/"
        t = os.path.join(p, dcim)
        try:
            if is_removable_drive_windows(l) and os.path.exists(t):
                cards.append(t)
        except Exception:
            pass
    return cards

def find_sd_cards_unix(dcim="DCIM"):
    cards = []
    for base in ("/media", "/Volumes", "/mnt"):
        if os.path.exists(base):
            for dev in os.listdir(base):
                t = os.path.join(base, dev, dcim)
                if os.path.isdir(t):
                    cards.append(t)
    return cards

def detect_sd_cards(dcim="DCIM"):
    return find_sd_cards_windows(dcim) if platform.system() == "Windows" else find_sd_cards_unix(dcim)


def load_flight_map(csv_path, delim="\t"):
    m = {}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for r in csv.reader(fh, delimiter=delim):
            if not r:
                continue
            kmz, dest = r[4].strip(), r[-1].strip()
            if kmz and dest:
                m[kmz.rsplit(".", 1)[0]] = dest
    return m


FLIGHT_ID_RE = re.compile(r"_([0-9]{2}-[A-Za-z0-9\-]+)$")

def flight_id(name):
    m = FLIGHT_ID_RE.search(Path(name).stem)
    return m.group(1) if m else None


def copy_file(src, dst_dir):
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / Path(src).name
    # shutil.move(src, dst)  # disabled: keep originals on SD‑card
    shutil.copy2(src, dst)
    print(f"✓ {src} → {dst}")


def distribute(dcim_root, fmap):
    for root, _d, files in os.walk(dcim_root):
        for f in files:
            fid = flight_id(f)
            if not fid or fid not in fmap:
                continue
            copy_file(os.path.join(root, f), fmap[fid])

if __name__ == "__main__":
    MAP_CSV = r"P:\\PheNo\\flight_catalog.csv"
    mapping = load_flight_map(MAP_CSV)
    for dcim in detect_sd_cards():
        distribute(dcim, mapping)