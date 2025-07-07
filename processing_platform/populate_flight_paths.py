#!/usr/bin/env python3
import os
import sys
import csv

# 1) Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'processing_platform.settings')
import django
django.setup()

from mainapp.models import Flight_Paths

def to_float(s):
    """Convert '2,00' or '3.14' → float, returning None on failure/empty."""
    if not s:
        return None
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def import_from_csv(csv_path):
    # Use utf-8-sig to drop any BOM on the first line
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        # DEBUG: uncomment to verify you see '#'
        # print("Detected headers:", reader.fieldnames)

        for row in reader:
            key = row.get('#')
            if not key or not key.strip().isdigit():
                # skip blank/garbage rows
                continue

            rn = int(key)
            data = {
                'record_number':        rn,
                'project':              row.get('Project') or None,
                'short_id':             row.get('Short_ID') or None,
                'project_folder_name':  row.get('Project Folder Name') or None,
                'field_folder_name':    row.get('Field folder name') or None,
                'flight_path_name':     row.get('Flight Path Name') or None,
                'location_of_field_plot': row.get('Location of field plot') or None,
                'type_of_flight':       row.get('Type of flight') or None,
                'frequency':            to_float(row.get('Frequency')),
                'drone_model':          row.get('Drone Model') or None,
                'flight_height':        to_float(row.get('Flight Height')),
                'flight_speed':         to_float(row.get('Flight Speed')),
                'side_overlap':         to_float(row.get('Side Overlap')),
                'front_overlap':        to_float(row.get('Front Overlap')),
                'camera_angle':         to_float(row.get('Camera Angle')),
                'flight_pattern':       row.get('Flight Pattern') or None,
                'flight_path_angle':    to_float(row.get('Flight Path Angle')),
                'ortho_gsd':            to_float(row.get('Ortho GSD')),
                'oblique_gsd':          to_float(row.get('Oblique GSD')),
                'flight_length':        to_float(row.get('Flight Length')),
                'ortho_gsd_pix4d':      to_float(row.get('Ortho GSD')),
                'oblique_gsd_pix4d':    to_float(row.get('Oblique GSD')),
                'first_flight_path':    row.get('1_flight path') or None,
                'pix4d_path':           row.get('2_1_pix4d path') or None,
            }

            obj, created = Flight_Paths.objects.update_or_create(
                record_number=rn,
                defaults=data
            )
            print(f"{'Created' if created else 'Updated'} record #{rn}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python populate_flight_paths.py path/to/Flight_list.csv")
        sys.exit(1)
    import_from_csv(sys.argv[1])
