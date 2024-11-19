import os
import streamlit as st
import time
import pandas as pd
import streamlit as st
import numpy as np

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
        #processing_paths["orthomosaics"] = find_files_in_folder(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic', 'tif')[0]
        processing_paths["orthomosaics"] = find_files_in_folder(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic', 'tif')
        processing_paths["DSM"] = find_files_in_folder(rf'{processing_paths["project"]}\3_dsm_ortho\1_dsm', 'tif')[0]
        processing_paths["indices"], processing_paths["indices_names"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')

        #df_log_file = import_log_file(rf'{processing_paths["project"]}\1_initial\report\html\index.html')

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
    df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()
    df_processing_status = df_processing_status.head(0)

    # Iterate over each row in df_flight_log
    for index, row in df_flight_log_merged.iterrows():
        processing_result = check_processing_status(row)
        new_row = create_new_row_for_processing_status(row, processing_result)
        #st.write(new_row)
        df_processing_status = pd.concat([df_processing_status, new_row], ignore_index=True)
    
    time_spent = round(time.time()-start_time, 2)
    st.write(f"Spent {time_spent}s going through {df_flight_log_merged.shape[0]} flights")
    st.write(df_processing_status)
    df_processing_status.to_csv("D:/PhenoCrop/0_csv/processing_status.csv", index=False)

def create_new_row_for_processing_status(flight_details, processing_result):
    # the flight_details argument needs to be a pandas series
    # the processing_result argument needs to be a dictionary
    indice_blue_exists = 1 if any("blue" in name.lower() for name in processing_result["indices_names"]) else 0
    indice_green_exists = 1 if any("green" in name.lower() for name in processing_result["indices_names"]) else 0
    indice_ndvi_exists = 1 if any("ndvi" in name.lower() for name in processing_result["indices_names"]) else 0
    indice_nir_exists = 1 if any("nir" in name.lower() for name in processing_result["indices_names"]) else 0
    indice_red_edge_exists = 1 if any("red_edge" in name.lower() for name in processing_result["indices_names"]) else 0
    indice_red_exists = 1 if any("red_red" in name.lower() for name in processing_result["indices_names"]) else 0
    DSM_exists = 0 if processing_result["DSM"] in [None, "", np.nan] else 1
    onging_status = 1 if flight_details["ongoing"] == 1 else 0

    if pd.isna(flight_details["coordinates_correct"]):
        coordinates_correct = " "
    else:
        coordinates_correct = flight_details["coordinates_correct"]

    processing_columns_for_image_types = {"3D": [DSM_exists],
                                      "MS": [indice_green_exists,indice_ndvi_exists,indice_nir_exists,indice_red_edge_exists,indice_red_exists],
                                      "phantom-MS": [indice_blue_exists,indice_green_exists,indice_ndvi_exists,indice_nir_exists,indice_red_edge_exists,indice_red_exists]}

    processed = 1
    for column in processing_columns_for_image_types[flight_details["image_type_keyword"]]:
        if column == 0:
            processed = 0

    new_row = pd.DataFrame([{"flight_output_path": flight_details["output_path"], "ProjectFolderPath": processing_result["project"], "Report": processing_result["report"],
                "Orthomosaics": processing_result["orthomosaics"], "Orthomosaics_names": processing_result["orthomosaics_names"], "DSM_Path": processing_result["DSM"],
                "DSM": DSM_exists, "Indices": processing_result["indices"], "Indices_names": processing_result["indices_names"], "Stats": processing_result["stats"],
                "Indice_blue": indice_blue_exists, "Indice_green": indice_green_exists, "Indice_ndvi": indice_ndvi_exists, "Indice_nir": indice_nir_exists,
                "Indice_red_edge": indice_red_edge_exists, "Indice_red": indice_red_exists, "processed": processed, "ongoing": onging_status,
                "coordinates_correct": coordinates_correct}])
    
    return new_row

if __name__ == "__main__":
    import pandas as pd
    import streamlit as st
    from file_system_functions import find_files_in_folder
    from file_system_functions import find_tif_files_in_subfolders
    from flight_log_preprocessing import preprocessing
    from flight_log_preprocessing import import_log_file

    update_all_flights()
else:
    from .file_system_functions import find_files_in_folder
    from .file_system_functions import find_tif_files_in_subfolders
    from .flight_log_preprocessing import preprocessing
    from .flight_log_preprocessing import import_log_file
