import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from modules.flight_log_preprocessing import preprocessing
import subprocess
import glob
import os
import sys

#st.set_page_config(layout="wide")
current_flight_ID = st.query_params["Index"]

df_flight_log, df_flight_routes, df_fields, df_flight_log_merged = preprocessing()

df_flight_log_merged['Index'] = range(1, len(df_flight_log_merged) + 1) # Creating a column telling whether the flight is the first, second, third, etc...

flight_details = df_flight_log_merged[df_flight_log_merged["flight_ID"] == current_flight_ID].iloc[0]
#flight_details

title_col_1, title_col_2 = st.columns([0.88,0.12])
with title_col_1:
    st.markdown(f"""
    # Nr {flight_details["Index"]}: &nbsp;{flight_details["date"]} &nbsp; {flight_details["Field ID"]}&nbsp; {flight_details["start_time"]} - {flight_details["end_time"]}""")

with title_col_2:
    st.text('')
    st.text('')
    #edit_mode = st.checkbox("✍")
    edit_mode = st.selectbox("Route Type", ["📖","✍"], label_visibility="collapsed")

body_column_1, body_column_2 = st.columns(2)
body_column_3, body_column_4 = st.columns(2)

#body_column_1_content = ["Step 1 Quality Check", "Quality checked by", "Workable Data", "Ready for next step (step 2 and 3)", "Ready for next step - person",
#                         "Step 2 processing", "Step 3 Image Stitching", "Processed by", "QGIS", "QGIS person"]

body_column_1_content = ["image_type_keyword", "drone", "drone_pilot", "CameraAngle", "Speed", "height", "BaseOverlap", "start_time", "end_time", "num_files", "num_dir"]

body_column_2_content = ["LongName", "ResearchHead", "Researcher", "VollebekkResponsible", "Location", "Crop", "Varieties", "Plots", "Length", "Width", "NitrogenLevels", "FlightFrequency"]

# Function to open the folder in the file explorer
def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

if (edit_mode == "📖"):
    #with body_column_1:
    #    flight_details_col_1 = flight_details[body_column_1_content]
    #    st.table(flight_details_col_1)

    with body_column_1:
        st.write("#### Flight")
        flight_details_col_1 = flight_details[body_column_1_content]
        st.table(flight_details_col_1)
        # Button to open the folder
        link_path = rf'{flight_details["output_path"]}'
        #link_path = rf'P:\PhenoCrop\1_flights\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
        if st.button('Go to image folder'):
            #st.write(f"Opened folder: {link_path}")
            open_folder(link_path)

    with body_column_2:
        st.write("#### Field")
        flight_details_col_2 = flight_details[body_column_2_content]
        st.table(flight_details_col_2)

if (edit_mode == "✍"):
    with body_column_1:
        st.write("#### Flight")
        flight_details_col_1 = flight_details[body_column_1_content]
        st.data_editor(flight_details_col_1)

    with body_column_2:
        st.write("#### Field")
        flight_details_col_2 = flight_details[body_column_2_content]
        st.table(flight_details_col_2)

st.write("#### Processing status")

# Function to find the tif file in a given folder
def find_tif_file(folder_path):
    tif_files = []
    tif_files.extend(glob.glob(os.path.join(folder_path, "**", "*.tif"), recursive=True))

    if tif_files == []:
        tif_files = [""]
    return tif_files

# Function to find the tif file in a given folder's subfolders (but not their subfolders)
def find_tif_files_in_subfolders(folder_path):
    tif_files = []
    if os.path.isdir(folder_path):
        # List all items in the given folder_path
        for item in os.listdir(folder_path):
            # Construct full path
            subdir_path = rf"{folder_path}\{item}"

            # Check if the item is a directory
            if os.path.isdir(subdir_path):
                # Look for .tif files in the current subdirectory
                found_tifs = glob.glob(os.path.join(subdir_path, "*.tif"))
                tif_files.extend(found_tifs)

    # Return list of .tif files found, or [""] if none were found
    if tif_files == []:
        tif_files = [""]
    return tif_files

def check_processing_status(flight_details):
    pix4d_path = rf'P:\PhenoCrop\2_pix4d\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
    flight_folder_name = os.path.basename(flight_details["output_path"])
    project_folder_paths = [rf'{pix4d_path}\{flight_folder_name}', rf'{pix4d_path}\{flight_folder_name}\{flight_folder_name}']
    processing_paths = {"project": "", "report": "", "orthomosaic": "", "DSM": "", "indices": [], "stats": ""}

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
        processing_paths["indices"] = find_tif_files_in_subfolders(rf'{processing_paths["project"]}\4_index\indices')
        
        # Displaying
        if st.button('Pix4DMapper folder'):
            open_folder(processing_paths["project"])

        for processing_name in ["report", "orthomosaic", "DSM", "indices"]:
            if processing_paths[processing_name] == "" or processing_paths[processing_name] == [""]:
                st.write(rf"{processing_name} does not exist")
            else:
                if isinstance(processing_paths[processing_name], list):
                    st.write(rf"{processing_name} exists")
                    st.write(processing_paths["indices"])
                else:
                    if st.button(processing_name):
                        open_folder(processing_paths[processing_name])

    # Write code to check for report, RGB mosaic, DSM and indices in the project folder paths.

check_processing_status(flight_details)