#!/usr/bin/env python3
import os
import sys
import csv
from pathlib import Path

# 1) Ensure Python can import your Django project
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 2) Bootstrap Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'processing_platform.settings')
import django
django.setup()

from mainapp.models import Flight_Paths

def to_float(s):
    if s is None:
        return None
    s = s.strip().replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def import_from_csv(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        return

    with csv_path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        print("Detected CSV headers:", reader.fieldnames)

        # pick your record-number column
        rec_cols = ['#', 'Record Number', 'record_number']
        for col in rec_cols:
            if col in reader.fieldnames:
                rec_col = col
                break
        else:
            print("ERROR: could not find any of", rec_cols)
            return

        # pick your flight-path-name column
        fpath_cols = ['Flight Path Name', 'flight_path_name', 'field_folder_name']
        for col in fpath_cols:
            if col in reader.fieldnames:
                fpath_col = col
                break
        else:
            print("ERROR: could not find any of", fpath_cols)
            return

        # now iterate
        for row in reader:
            rec = row.get(rec_col, '').strip()
            if not rec.isdigit():
                continue
            rn = int(rec)

            fpn = row.get(fpath_col, '').strip() or None
            data = {
                'flight_path_name':   fpn,
                'short_id':           row.get('Short_ID') or None,
                'first_flight_path':  row.get('1_flight path') or None,
                'pix4d_path':         row.get('2_1_pix4d path') or None,
                'side_overlap':       to_float(row.get('Side Overlap')),
                'front_overlap':      to_float(row.get('Front Overlap')),
                'flight_height':      to_float(row.get('Flight Height')),
                # … add more mappings here as needed …
            }

            obj, created = Flight_Paths.objects.update_or_create(
                record_number=rn,
                defaults=data
            )
            print(f"{'Created' if created else 'Updated'} Flight_Paths id={obj.id} (record_number={rn})")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python populate_flight_paths.py path/to/your.csv")
        sys.exit(1)
    import_from_csv(sys.argv[1])
