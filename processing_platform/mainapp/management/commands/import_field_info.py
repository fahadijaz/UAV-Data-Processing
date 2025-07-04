from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand
from mainapp.models import Fields


class Command(BaseCommand):
    help = "Import field records from Excel sheet"

    def add_arguments(self, parser):
        parser.add_argument("excel_file", type=str, help="Path to Excel file")

    def handle(self, *args, **kwargs):
        file_path = kwargs["excel_file"]
        df = pd.read_excel(file_path, dtype=str).fillna("")

        for index, row in df.iterrows():
            # Skip rows where all values are blank
            if not any(str(value).strip() for value in row.values):
                continue

            def parse_date(date_str):
                try:
                    return pd.to_datetime(date_str).date() if date_str else None
                except Exception:
                    return None

            start_date = parse_date(row.get("Start date", ""))
            end_date = parse_date(row.get("End date", ""))

            submission_id = row.get("$submission_id", "").strip()
            long_id = row.get("Longer ID (used for folder names)", "").strip()

            # Use submission_id if available, else long_id to match existing records
            unique_filter = {}
            if submission_id:
                unique_filter["submission_id"] = submission_id
            elif long_id:
                unique_filter["long_id"] = long_id
            else:
                self.stdout.write(
                    f"Skipping row {index + 2}: No unique identifier (submission_id or long_id)"
                )
                continue

            field, created = Fields.objects.update_or_create(
                **unique_filter,
                defaults={
                    "project": row.get("Project"),
                    "short_id": row.get("Short_ID"),
                    "long_id": long_id,
                    "crop": row.get("Crop"),
                    "location_of_field_plot": row.get("Location of field plot"),
                    "multispectral": row.get("Multispectral Imaging"),
                    "three_dimensional": row.get(
                        "3D Mapping (Plant Height estimation)"
                    ),
                    "thermal": row.get("Thermal Imaging"),
                    "rgb": row.get("RGB"),
                    "flying_frequency": row.get("Frequency"),
                    "start_date": start_date,
                    "end_date": end_date,
                    "created_at": row.get("$created"),
                    "name": row.get("Name"),
                    "department": row.get("Department / institution"),
                    "email": row.get("E-mail Address"),
                    "project_number": row.get("Project number"),
                    "description": row.get("Description"),
                    "data_delivery_method": row.get("Data Delivery Method"),
                    "vollebekk_responsible": row.get("Vollebekk Responsible"),
                    "sowing_date": row.get("Sowing Date"),
                    "measuring_ground_level": row.get("Measuring Ground Level"),
                },
            )

            if created:
                self.stdout.write(f"Created new record for: {submission_id or long_id}")
            else:
                self.stdout.write(f"Updated record for: {submission_id or long_id}")
