from Pix4D_cleaning_fucnt import *

# Import all CSV Logs
# Loading and preprocessing datasets
df_flight_log = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_log.csv")
df_flight_routes = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_routes.csv")
df_fields = pd.read_csv("P:\\PhenoCrop\\0_csv\\fields.csv")
df_processing_status = pd.read_csv("P:\\PhenoCrop\\0_csv\\processing_status.csv")


field_ids = df_fields["Field ID"].tolist()
flight_types =  sorted(list(set(df_flight_routes["BaseType"].dropna())))
field_ids, flight_types

src_drive = r"P:\\"
dest_drive = r"D:\\"
path_pix4d_gnrl = r"PhenoCrop\2_pix4d"
field_id = field_ids[0]
flight_type = flight_types[1]
dest_path = os.path.join(dest_drive,path_pix4d_gnrl,field_id,flight_type)
src_drive, dest_drive, path_pix4d_gnrl, field_id, flight_type, dest_path

proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_ids, flight_types)
log_not_found = copy_p4d_log(dest_path, pix4d_path_src)
pdf_report_not_found, report_does_not_exists, report_name_different = copy_reports(dest_path, proj_dict)
ortho_not_found_dict, ortho_found_dict, mesh_extra_found_dict = copy_ortho(dest_path, proj_dict, chk_size=True, type_of_data_to_copy=["ortho_primary", "dsm_dtm", "mesh_extras"])

proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type)
log_not_found = copy_p4d_log(dest_drive, pix4d_path_src)
print(field_id, flight_type, pix4d_path_src)

# proj_dict, pix4d_path_src = create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type)