from Pix4D_cleaning_fucnt import *
import os
import pandas as pd
import itertools


# Import all CSV Logs
# Loading and preprocessing datasets
df_flight_log = pd.read_csv("D:\\PhenoCrop\\0_csv\\flight_log.csv")
df_flight_routes = pd.read_csv("D:\\PhenoCrop\\0_csv\\flight_routes.csv")
df_fields = pd.read_csv("D:\\PhenoCrop\\0_csv\\fields.csv")
df_processing_status = pd.read_csv("D:\\PhenoCrop\\0_csv\\processing_status.csv")


# field_ids = df_fields["Field ID"].tolist()
flight_types =  sorted(list(set(df_flight_routes["BaseType"].dropna())))
flight_types = ['MS', '3D']
flight_types = ['3D']
# field_ids = ['PRO_BAR_VOLL', 'DIVERSITY_OATS', 'OAT_FRONTIERS', 'PILOT', 'E166', 'PRO_BAR_SØRÅS', 'PHENO_CROP']
field_ids = ['E166']
field_ids, flight_types

src_drive = r"P:\\"
dest_drive = r"D:\\"
path_pix4d_gnrl = r"PhenoCrop\2_pix4d"
type_of_data_to_copy=["ortho_primary","ortho_extra", "dsm_dtm", "mesh_extras"]

# Naming the file for backing up the status of copy progress
state_file = "proj_dict_state_temp.json"

# Generate a dictionary with all combinations
field_data_combinations = {f"{key}_{value}": (key, value) for key, value in itertools.product(field_ids, flight_types)}
field_data_combinations_keys = list(field_data_combinations.keys())

# Adding a fail safe in case the copying fails mid copy. If proj_dict already exists, then do not go through this step. 
# Rather go to else and resume copying from the last project being copied.

if os.path.exists(state_file):
    # Load proj_dict temp status file if it exists, in case the run was stopped in the middle
    
    proj_dict, combination = load_proj_data(state_file)
    field_data_combinations, comb_temp = load_proj_data("field_data_combinations.json")
    field_data_combinations_keys = list(field_data_combinations.keys())
    
    print("Resuming copying from the project", proj_dict.keys())
    field_id = combination[0]
    flight_type = combination[1]
    dest_path = os.path.join(dest_drive, path_pix4d_gnrl, field_id, flight_type)
    pix4d_path_src = os.path.join(src_drive, path_pix4d_gnrl, field_id, flight_type)

    log_not_found = copy_p4d_log(dest_path, pix4d_path_src)
    pdf_report_not_found, report_does_not_exists, report_name_different = copy_reports(dest_path, proj_dict)
    ortho_found_dict, mesh_found_dict, mesh_extra_found_dict = copy_ortho(dest_path, proj_dict, combination, state_file, chk_size=True, type_of_data_to_copy=type_of_data_to_copy)

else:
    print("Starting copying from start. proj_dict does not exist.")


for key in field_data_combinations_keys:
    combination = field_data_combinations[key]
    field_id = combination[0]
    flight_type = combination[1]
    print(field_data_combinations, combination)

    # Deleting the field_datatype from the field_data_combinations
    del field_data_combinations[key]

    # Need to be able to backup field_data_combinations as well and restore if it exists
    save_proj_data(field_data_combinations, combination, "field_data_combinations.json")

    dest_path = os.path.join(dest_drive, path_pix4d_gnrl, field_id, flight_type)
    print(f"""
        Begining of processing new field
        Source Drive: {src_drive}
        Destination Drive: {dest_drive}
        Pix4D General Path: {path_pix4d_gnrl}
        Field ID: {field_id}
        Flight Type: {flight_type}
        Destination Path: {dest_path}
        """)
    

    proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type)
    save_proj_data(proj_dict, combination, state_file)
    proj_dict, combination = load_proj_data(state_file)

    log_not_found = copy_p4d_log(dest_path, pix4d_path_src)
    pdf_report_not_found, report_does_not_exists, report_name_different = copy_reports(dest_path, proj_dict)
    
    ortho_found_dict, mesh_found_dict, mesh_extra_found_dict = copy_ortho(dest_path, proj_dict, combination, state_file, chk_size=True, type_of_data_to_copy=type_of_data_to_copy)

    print(proj_dict)

    print(f"""
        Copying complete!
        Source Drive: {src_drive}
        Field ID: {field_id}
        Flight Type: {flight_type}
        Destination Path: {dest_path}
        """)