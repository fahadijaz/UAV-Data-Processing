import os
from .file_system_functions import find_tif_file
from .file_system_functions import find_tif_files_in_subfolders
from .flight_log_preprocessing import preprocessing

# A function to check which processing outputs exist for a flight
def check_processing_status(flight_details):
    pix4d_path = rf'P:\PhenoCrop\2_pix4d\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
    flight_folder_name = os.path.basename(flight_details["output_path"])
    project_folder_paths = [rf'{pix4d_path}\{flight_folder_name}', rf'{pix4d_path}\{flight_folder_name}\{flight_folder_name}']
    processing_paths = {"project": "", "report": "", "orthomosaic": "", "DSM": "", "indices": [], "indices_names": [], "stats": ""}

    # Finding project path
    for project_path_check in project_folder_paths:
        if os.path.isdir(project_path_check):
            processing_paths["project"] = project_path_check
    
    if processing_paths["project"] != "":
        # Finding the other processing paths based on the project path
        processing_paths["report"] = rf'{processing_paths["project"]}\1_initial\report\html\index.html'
        processing_paths["orthomosaic"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic')[0]
        processing_paths["DSM"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\1_dsm')[0]
        processing_paths["indices"], processing_paths["indices_names"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')
    
    return processing_paths

def update_all_flights():
    # This function is going to goi through all flights and update their processing status
    df_flight_log, df_flight_routes, df_fields, df_flight_log_merged = preprocessing()

if __name__ == "__main__":
    #update_all_flights()
    pass
