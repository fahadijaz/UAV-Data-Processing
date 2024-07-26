import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from modules.flight_log_preprocessing import preprocessing

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

if (edit_mode == "📖"):
    #with body_column_1:
    #    flight_details_col_1 = flight_details[body_column_1_content]
    #    st.table(flight_details_col_1)

    with body_column_1:
        st.write("&nbsp; Flight")
        flight_details_col_1 = flight_details[body_column_1_content]
        st.table(flight_details_col_1)

    with body_column_2:
        st.write("&nbsp; Field")
        flight_details_col_2 = flight_details[body_column_2_content]
        st.table(flight_details_col_2)

if (edit_mode == "✍"):
    with body_column_1:
        st.write("&nbsp; Flight")
        flight_details_col_1 = flight_details[body_column_1_content]
        st.data_editor(flight_details_col_1)

    with body_column_2:
        st.write("&nbsp; Field")
        flight_details_col_2 = flight_details[body_column_2_content]
        st.table(flight_details_col_2)
