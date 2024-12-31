from storage_functions import *
from Pix4D_cleaning_fucnt import *
import os
import pandas as pd
import itertools

# Import all CSV Logs
# Loading and preprocessing datasets
df_flight_log = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_log.csv")
df_flight_routes = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_routes.csv")
df_fields = pd.read_csv("P:\\PhenoCrop\\0_csv\\fields.csv")
df_processing_status = pd.read_csv("P:\\PhenoCrop\\0_csv\\processing_status.csv")


# field_ids = df_fields["Field ID"].tolist()
flight_types =  sorted(list(set(df_flight_routes["BaseType"].dropna())))
field_ids = ['PRO_BAR_VOLL', 'DIVERSITY_OATS', 'OAT_FRONTIERS', 'PILOT', 'E166', 'PRO_BAR_SØRÅS', 'PHENO_CROP']
field_ids, flight_types

src_drive = r"P:\\"
path_pix4d_gnrl = r"PhenoCrop\2_pix4d"

# Generate a dictionary with all combinations
field_data_combinations = {f"{key}_{value}": (key, value) for key, value in itertools.product(field_ids, flight_types)}

for key, combination  in field_data_combinations.items():
    field_id = combination[0]
    flight_type = combination[1]
    print(f"""
        Begining of processing new field
        Source Drive: {src_drive}
        Pix4D General Path: {path_pix4d_gnrl}
        Field ID: {field_id}
        Flight Type: {flight_type}
        """)
    
    proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type)
    
    if proj_dict:
        data = "pix4d"
        folder_sizes = measure_folders_size(proj_dict)
        append_dict_to_csv(folder_sizes, field_id+flight_type, file_name='Pix4d_Size.csv')

        # Getting size of flights
        data = "flights"
        updated_proj_dict = {k: [v[0].replace("2_pix4d", "1_flights")] for k, v in proj_dict.items()}
        folder_sizes_flights = measure_folders_size(updated_proj_dict)
        append_dict_to_csv(folder_sizes_flights, field_id+"_"+flight_type+"_"+data, file_name='Flights_Size.csv')

        # Getting number of images in each flight
        data = "number-of-images"
        extension = [".jpg", ".tif"]
        file_counts = count_files_in_folders(updated_proj_dict, extension)
        append_dict_to_csv(file_counts, field_id+"_"+flight_type+"_"+data, file_name='Count_Images.csv')
        
    print(f"""
        Copying complete!
        Source Drive: {src_drive}
        Field ID: {field_id}
        Flight Type: {flight_type}
        """)