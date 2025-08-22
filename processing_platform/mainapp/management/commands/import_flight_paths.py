import csv
import re
from django.core.management.base import BaseCommand
from mainapp.models import Flight_Paths


class Command(BaseCommand):
    help = 'Import flight paths from flight_list.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to flight_list.csv')

    def handle(self, *args, **options):
        imported_count = 0
        skipped_count = 0
        
        with open(options['csv_file'], 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            headers = next(reader)
            
            for row in reader:
                if not row or not row[0] or not row[5]:
                    skipped_count += 1
                    continue
                
                try:
                    flight_path_original = row[5].strip()
                    
                    flight_path_clean = flight_path_original.replace('.kmz', '')
                    
                    
                    flight_height_str = row[10].replace('m', '') if row[10] else ''
                    flight_height = float(flight_height_str) if flight_height_str and flight_height_str.replace('.', '').isdigit() else None
                    
                    side_overlap = float(row[12]) if row[12] and row[12].replace('.', '').isdigit() else None
                    front_overlap = float(row[13]) if row[13] and row[13].replace('.', '').isdigit() else None
                    
                    def clean_float(value):
                        if not value or value in ['#I/T', '#VERDI!', '']:
                            return None
                        try:
                            return float(value.replace(',', '.'))
                        except (ValueError, AttributeError):
                            return None
                    
                    Flight_Paths.objects.get_or_create(
                        flight_path_name=flight_path_clean,
                        defaults={
                            'record_number': int(row[0]) if row[0] and row[0].isdigit() else None,
                            'project': row[1] or '',
                            'short_id': row[2] or '',
                            'project_folder_name': row[3] or '',
                            'field_folder_name': row[4] or '',
                            'location_of_field_plot': row[6] or '',
                            'type_of_flight': row[7] or '',
                            'frequency': clean_float(row[8]),
                            'drone_model': row[9] or '',
                            'flight_height': flight_height,
                            'flight_speed': clean_float(row[11]),
                            'side_overlap': side_overlap,
                            'front_overlap': front_overlap,
                            'camera_angle': clean_float(row[14]),
                            'flight_pattern': row[15] or '',
                            'flight_path_angle': clean_float(row[16]),
                            'ortho_gsd': clean_float(row[17]),
                            'oblique_gsd': clean_float(row[18]),
                            'flight_length': clean_float(row[19]),
                            'ortho_gsd_pix4d': clean_float(row[20]),
                            'oblique_gsd_pix4d': clean_float(row[21]),
                            'first_flight_path': row[22] or '',
                            'pix4d_path': row[23] or '',
                        }
                    )
                    imported_count += 1
                    self.stdout.write(f"Imported: {flight_path_clean}")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error importing row {row}: {e}")
                    )
                    skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully imported {imported_count} flight paths, skipped {skipped_count}'
            )
        )
        
        self.stdout.write("\nImported flight paths:")
        for fp in Flight_Paths.objects.all()[:10]:
            self.stdout.write(f"- {fp.flight_path_name}")