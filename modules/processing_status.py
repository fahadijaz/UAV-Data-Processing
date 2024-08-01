import os
import streamlit as st
from .file_system_functions import open_folder
from .file_system_functions import find_tif_file
from .file_system_functions import find_tif_files_in_subfolders

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
    
    if processing_paths["project"] == "":
        st.write("Project folder does not exist")
    else:
        # Finding the other processing paths based on the project path
        processing_paths["report"] = rf'{processing_paths["project"]}\1_initial\report\html\index.html'
        processing_paths["orthomosaic"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\2_mosaic')[0]
        processing_paths["DSM"] = find_tif_file(rf'{processing_paths["project"]}\3_dsm_ortho\1_dsm')[0]
        processing_paths["indices"], processing_paths["indices_names"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')
        
        # Displaying processing status
        if st.button('Pix4DMapper folder'):
            open_folder(processing_paths["project"])
        
        # Looping through each of the potential processing outputs and displaying their status
        for processing_name in ["report", "orthomosaic", "DSM", "indices"]:
            if processing_paths[processing_name] == "" or processing_paths[processing_name] == [""]:
                st.write(rf"{processing_name} does not exist")
            else:
                if isinstance(processing_paths[processing_name], list):
                    indices_names = ""
                    for index, indice_name in enumerate(processing_paths["indices_names"]):
                        if index == 0:
                            indices_names = rf"{indice_name}"
                        else:
                            indices_names = rf"{indices_names}, {indice_name}"
                    st.write(rf"{processing_name} ({indices_names}) exists")
                else:
                    if st.button(processing_name):
                        open_folder(processing_paths[processing_name])

    # Write code to check for report, RGB mosaic, DSM and indices in the project folder paths.
