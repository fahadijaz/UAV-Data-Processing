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
# field_ids = ['PRO_BAR_VOLL', 'DIVERSITY_OATS', 'OAT_FRONTIERS', 'PILOT', 'E166', 'PRO_BAR_SØRÅS', 'PHENO_CROP']
field_ids = ['PILOT', 'PRO_BAR_VOLL', 'DIVERSITY_OATS', 'OAT_FRONTIERS', 'E166', 'PRO_BAR_SØRÅS', 'PHENO_CROP']
field_ids, flight_types

src_drive = r"P:\\"
dest_drive = r"D:\\"
path_pix4d_gnrl = r"PhenoCrop\2_pix4d"

# Generate a dictionary with all combinations
field_data_combinations = {f"{key}_{value}": (key, value) for key, value in itertools.product(field_ids, flight_types)}

for key, combination  in field_data_combinations.items():
    field_id = combination[0]
    flight_type = combination[1]
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
    
    # type_of_data_to_copy=["ortho_primary","ortho_extra", "dsm_dtm", "mesh_extras"]

    proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type)
    log_not_found = copy_p4d_log(dest_path, pix4d_path_src)
    pdf_report_not_found, report_does_not_exists, report_name_different = copy_reports(dest_path, proj_dict)
    ortho_found_dict, mesh_found_dict, mesh_extra_found_dict = copy_ortho(dest_path, proj_dict, chk_size=True, type_of_data_to_copy=["ortho_primary","ortho_extra", "dsm_dtm", "mesh_extras"])


    print(f"""
        Copying complete!
        Source Drive: {src_drive}
        Field ID: {field_id}
        Flight Type: {flight_type}
        Destination Path: {dest_path}
        """)