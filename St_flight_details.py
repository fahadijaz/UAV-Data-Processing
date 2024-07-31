import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from modules.flight_log_preprocessing import preprocessing
import subprocess
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

def check_pix4D_processing_status(flight_details):
    pix4d_path = rf'P:\PhenoCrop\2_pix4d\{flight_details["Field ID"]}\{flight_details["BaseType"]}'
    flight_folder_name = os.path.basename(flight_details["output_path"])
    project_folder_paths = [rf'{pix4d_path}\{flight_folder_name}', rf'{pix4d_path}\{flight_folder_name}\{flight_folder_name}']
    project_path = ""
    report_path = ""
    for project_path_check in project_folder_paths:
        if os.path.isdir(project_path_check):
            project_path = project_path_check
    
    if project_path == "":
        st.write("Project folder does not exist")
    else:
        if st.button('Pix4DMapper folder'):
            open_folder(project_path)
        report_path = rf'{project_path}\1_initial\report\html\index.html'
    
    if report_path == "":
        st.write("Report does not exist")
    else:
        if st.button('Report'):
            open_folder(report_path)
    # Write code to check for report, RGB mosaic, DSM and indices in the project folder paths.

check_pix4D_processing_status(flight_details)