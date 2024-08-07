import os
import streamlit as st
import time

# A function to check which processing outputs exist for a flight.
# It returns a dictionary with information like e.g. paths.
def check_processing_status(flight_details):
    pix4d_path = rf'P:\PhenoCrop\2_pix4d\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
    flight_folder_name = os.path.basename(flight_details["output_path"])
    project_folder_paths = [rf'{pix4d_path}\{flight_folder_name}', rf'{pix4d_path}\{flight_folder_name}\{flight_folder_name}']
    processing_paths = {"project": "", "report": "", "orthomosaics": [], "orthomosaics_names": [], "DSM": "", "indices": [], "indices_names": [], "stats": ""}

    # Finding project path
    for project_path_check in project_folder_paths:
        if os.path.isdir(project_path_check):
            processing_paths["project"] = project_path_check
    
    if processing_paths["project"] != "":
        # Finding the other processing paths based on the project path
        processing_paths["report"] = rf'{processing_paths["project"]}\1_initial\report\html\index.html'
        #processing_paths["orthomosaics"] = find_tif_files(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic')[0]
        processing_paths["orthomosaics"] = find_tif_files(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic')
        processing_paths["DSM"] = find_tif_files(rf'{processing_paths["project"]}\3_dsm_ortho\1_dsm')[0]
        processing_paths["indices"], processing_paths["indices_names"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')

        # This loops through processing_paths["orthomosaics"] to find the names of the orthomosaics
        for ortho_path in processing_paths["orthomosaics"]:
            # Splits the filename based on underscores and takes the last part
            ortho_name = ortho_path.split('_')[-1]
            ortho_name = ortho_name.replace('.tif', '')
            processing_paths["orthomosaics_names"].append(ortho_name)
    
    return processing_paths

def update_all_flights():
    start_time = time.time()
    # This function is going to go through all flights and update their processing status
    df_flight_log, df_flight_routes, df_fields, df_flight_log_merged = preprocessing()
    df_processing_status = pd.read_csv("P:\\PhenoCrop\\0_csv\\processing_status.csv")

    # Iterate over each row in df_flight_log
    for index, row in df_flight_log_merged.iterrows():
        processing_result = check_processing_status(row)
        new_row = pd.DataFrame([{"flight_output_path": row["output_path"], "ProjectFolderPath": processing_result["project"], "Report": processing_result["report"],
                    "Orthomosaics": processing_result["orthomosaics"], "Orthomosaics_names": processing_result["orthomosaics_names"], "DSM_Path": processing_result["DSM"],
                    "Indices": processing_result["indices"], "Indices_names": processing_result["indices_names"], "Stats": processing_result["stats"]}])
        #st.write(new_row)
        df_processing_status = pd.concat([df_processing_status, new_row], ignore_index=True)
    
    time_spent = round(time.time()-start_time, 2)
    st.write(f"Spent {time_spent}s going through {df_flight_log_merged.shape[0]} flights")
    st.write(df_processing_status)
    df_processing_status.to_csv("P:/PhenoCrop/0_csv/processing_status.csv", index=False)


if __name__ == "__main__":
    import pandas as pd
    import streamlit as st
    from file_system_functions import find_tif_files
    from file_system_functions import find_tif_files_in_subfolders
    from flight_log_preprocessing import preprocessing

    update_all_flights()
else:
    from .file_system_functions import find_tif_files
    from .file_system_functions import find_tif_files_in_subfolders
    from .flight_log_preprocessing import preprocessing
