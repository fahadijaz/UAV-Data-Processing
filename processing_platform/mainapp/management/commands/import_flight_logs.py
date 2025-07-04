from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand
from mainapp.models import Flight_Log


class Command(BaseCommand):
    help = "Import flight logs from Excel sheet"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Path to Excel file")

    def handle(self, *args, **kwargs):
        file_path = kwargs["excel_file"]
        df = pd.read_excel(file_path, sheet_name="Flight Log", dtype=str)

        for index, row in df.iterrows():
            flight_date_str = row.get("Flight Date")
            if pd.notna(flight_date_str):
                flight_date = pd.to_datetime(flight_date_str).date()
            else:
                flight_date = None

            log, created = Flight_Log.objects.update_or_create(
                foldername=row.get("Foldername"),
                flight_date=flight_date,
                defaults={
                    "flight_field_id": row.get("Flight Field ID"),
                    "project": row.get("Project"),
                    "flight_type": row.get("Route type (MS, 3D, Thermal, RGB)"),
                    "drone_type": row.get("Drone Model"),
                    "drone_pilot": row.get("Drone Pilot"),
                    "reflectance_panel": row.get("Reflectance Panel (New/Old)"),
                    "flight_start": row.get("Flight Start"),
                    "flight_endstart": row.get("Flight End"),
                    "flight_comments": row.get("Flight Comments"),
                    "p4d_step1": row.get("Step 1 P4D Proj."),
                    "p4d_step1_done_by": row.get("Done by"),
                    "p4d_step1_workable_data": row.get("Workable Data"),
                    "p4d_processing": row.get("P4D Processing"),
                    "p4d_processing_done_by": row.get(
                        "Done by.1"
                    ),  # Watch for duplicate "Done by"
                    "p4d_processing_pc": row.get("PC Used"),
                    "p4d_processing_comments": row.get("Processing Comments"),
                    "flight_height": row.get("Flight Height"),
                    "flight_side_over": row.get("Side Overlap"),
                    "flight_front_over": row.get("Front Overlap"),
                    "flight_wind_speed": row.get("Wind (m/s)"),
                    "flight_drone_type": row.get("Drone type"),
                    "new_folder_name": row.get("New folder name"),
                    "root_folder": row.get("Root Folder"),
                    "flight_path": row.get("Flight path"),
                    "p4d_path": row.get("Pix4D path"),
                },
            )

            if created:
                self.stdout.write(f"Created new record for {row.get('Foldername')}")
            else:
                self.stdout.write(f"Updated record for {row.get('Foldername')}")
