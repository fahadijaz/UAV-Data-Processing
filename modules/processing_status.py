import os

# A function to check which processing outputs exist for a flight.
# It returns a dictionary with information lik e.g. paths.
def check_processing_status(flight_details):
    pix4d_path = rf'P:\PhenoCrop\2_pix4d\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
    flight_folder_name = os.path.basename(flight_details["output_path"])
    project_folder_paths = [rf'{pix4d_path}\{flight_folder_name}', rf'{pix4d_path}\{flight_folder_name}\{flight_folder_name}']
    processing_paths = {"project": "", "report": "", "orthomosaics": "", "DSM": "", "indices": [], "indices_names": [], "stats": ""}

    # Finding project path
    for project_path_check in project_folder_paths:
        if os.path.isdir(project_path_check):
            processing_paths["project"] = project_path_check
    
    if processing_paths["project"] != "":
        # Finding the other processing paths based on the project path
        processing_paths["report"] = rf'{processing_paths["project"]}\1_initial\report\html\index.html'
        processing_paths["orthomosaics"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic')[0]
        processing_paths["DSM"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\1_dsm')[0]
        processing_paths["indices"], processing_paths["indices_names"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')
    
    return processing_paths

def update_all_flights():
    # This function is going to go through all flights and update their processing status
    df_flight_log, df_flight_routes, df_fields, df_flight_log_merged = preprocessing()
    df_processing_status = pd.read_csv("P:\\PhenoCrop\\0_csv\\processing_status.csv")

    st.write(df_flight_log_merged)

    # Iterate over each row in df_flight_log
    for index, row in df_flight_log_merged.iterrows():
        processing_result = check_processing_status(row)
        new_row = [row["output_path"], processing_result["project"], processing_result["report"], processing_result["orthomosaics"],
                    processing_result["DSM"], processing_result["indices"], processing_result["indices_names"], processing_result["stats"]]
        df_processing_status = pd.concat([df_processing_status, processing_result], ignore_index=True)
    
    st.write(df_processing_status)

if __name__ == "__main__":
    import pandas as pd
    import streamlit as st
    from file_system_functions import find_tif_file
    from file_system_functions import find_tif_files_in_subfolders
    from flight_log_preprocessing import preprocessing

    update_all_flights()
else:
    from .file_system_functions import find_tif_file
    from .file_system_functions import find_tif_files_in_subfolders
    from .flight_log_preprocessing import preprocessing
