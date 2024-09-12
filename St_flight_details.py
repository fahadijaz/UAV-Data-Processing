import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from modules.flight_log_preprocessing import preprocessing
from modules.processing_status import check_processing_status
from modules.processing_status import create_new_row_for_processing_status
from modules.file_system_functions import open_folder

current_flight_ID = st.query_params["Index"]

df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()

df_flight_log_merged['Index'] = range(1, len(df_flight_log_merged) + 1) # Creating a column telling whether the flight is the first, second, third, etc...

# Getting a list of the row in df_flight_log_merged that corresponds with this flight
flight_details = df_flight_log_merged[df_flight_log_merged["flight_ID"] == current_flight_ID].iloc[0]
#st.write(flight_details)

processing_paths = check_processing_status(flight_details)

def display_processing_status(processing_paths):
    if processing_paths["project"] == "":
        st.write("Project folder does not exist")
        return
    
    # Displaying processing status
    if st.button('Pix4DMapper folder'):
        open_folder(processing_paths["project"])
    
    # Looping through each of the potential processing outputs and displaying their status
    for processing_name in ["report", "orthomosaics", "DSM", "indices"]:
        if processing_paths[processing_name] == "" or processing_paths[processing_name] == [""] or processing_paths[processing_name] == []:
            st.write(rf"{processing_name} does not exist")
        else:
            if isinstance(processing_paths[processing_name], list):
                names = ""
                names_key = f"{processing_name}_names"
                for index, name in enumerate(processing_paths[names_key]):
                    if index == 0:
                        names = rf"{name}"
                    else:
                        names = rf"{names}, {name}"
                st.write(rf"{processing_name} ({names}) exists")
            else:
                if st.button(processing_name):
                    open_folder(processing_paths[processing_name])

# Updates this flight's row in the processing status csv
def update_this_processing_status(df_processing_status, flight_details, processing_paths):
    old_processing_status = df_processing_status[df_processing_status["flight_output_path"] == flight_details["output_path"]]

    # Create new_processing_status DataFrame with one row
    new_processing_status = create_new_row_for_processing_status(flight_details, processing_paths)

    # Find the index of the row that matches 'flight_output_path'
    index_to_replace = df_processing_status[df_processing_status["flight_output_path"] == flight_details["output_path"]].index

    if (df_processing_status["flight_output_path"] == flight_details["output_path"]).any():
        # Replace the row(s) at the found index with the new data
        df_processing_status.loc[index_to_replace, :] = new_processing_status.values
    else:
        df_processing_status = pd.concat([df_processing_status, new_processing_status], ignore_index=True)
    
    # Save the updated DataFrame back to the CSV file
    df_processing_status.to_csv("P:/PhenoCrop/0_csv/processing_status.csv", index=False)


def display_section_title():
    global edit_mode
    title_col_1, title_col_2 = st.columns([0.88,0.12])
    with title_col_1:
        st.markdown(f"""
        # Nr {flight_details["Index"]}: &nbsp;{flight_details["date"]} &nbsp; {flight_details["Field ID"]}&nbsp; {flight_details["start_time"]} - {flight_details["end_time"]}""")

    with title_col_2:
        st.text('')
        st.text('')
        #edit_mode = st.checkbox("✍")
        edit_mode = st.selectbox("Route Type", ["📖","✍"], label_visibility="collapsed")

def display_section_main_1():
    global edit_mode

    body_column_1, body_column_2 = st.columns(2)
    body_column_3, body_column_4 = st.columns(2)

    #body_column_1_content = ["Step 1 Quality Check", "Quality checked by", "Workable Data", "Ready for next step (step 2 and 3)", "Ready for next step - person",
    #                         "Step 2 processing", "Step 3 Image Stitching", "Processed by", "QGIS", "QGIS person"]

    body_column_1_content = ["image_type_keyword", "drone", "drone_pilot", "CameraAngle", "Speed", "height", "BaseOverlap", "start_time", "end_time", "num_files", "num_dir"]

    body_column_2_content = ["LongName", "ResearchHead", "Researcher", "VollebekkResponsible", "Location", "Crop", "Varieties", "Plots", "Length", "Width", "NitrogenLevels", "FlightFrequency"]

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

def display_section_processing_status():
    # Sets the default value for the ongoing status field
    default_ongoing_value = ""  # Default to empty string if condition is not met
    if flight_details["ongoing"] == 1:
        default_ongoing_value = "ongoing"
    
    # Sets the default value for the coordinates status field
    default_coordinates_value = " "  # Default to empty string if condition is not met
    if flight_details["coordinates_correct"] == "coordinates incorrect":
        default_coordinates_value = "coordinates incorrect"
    if flight_details["coordinates_correct"] == "coordinates correct":
        default_coordinates_value = "coordinates correct"

    processing_title_column_1, processing_title_column_2, processing_title_column_3 = st.columns([0.55, 0.18, 0.27])
    with processing_title_column_1:
        st.write("#### Processing status")
    
    with processing_title_column_2:
        input_ongoing = st.selectbox("Processing ongoing?", ["","ongoing"], label_visibility="collapsed", index=["", "ongoing"].index(default_ongoing_value))
    
    with processing_title_column_3:
        input_coordinates = st.selectbox("Coordinates correct?", [" ", "coordinates incorrect", "coordinates correct"], label_visibility="collapsed", index=[" ", "coordinates incorrect", "coordinates correct"].index(default_coordinates_value))
    
    if input_ongoing == "ongoing":
        flight_details["ongoing"] = 1
        update_this_processing_status(df_processing_status, flight_details, processing_paths)
    
    if input_ongoing == "":
        flight_details["ongoing"] = 0
        update_this_processing_status(df_processing_status, flight_details, processing_paths)
        
    if input_coordinates == " ":
        flight_details["coordinates_correct"] = " "
        update_this_processing_status(df_processing_status, flight_details, processing_paths)
        
    if input_coordinates == "coordinates incorrect":
        flight_details["coordinates_correct"] = "coordinates incorrect"
        update_this_processing_status(df_processing_status, flight_details, processing_paths)
        
    if input_coordinates == "coordinates correct":
        flight_details["coordinates_correct"] = "coordinates correct"
        update_this_processing_status(df_processing_status, flight_details, processing_paths)

    update_this_processing_status(df_processing_status, flight_details, processing_paths)
    display_processing_status(processing_paths)

display_section_title()
display_section_main_1()
display_section_processing_status()
