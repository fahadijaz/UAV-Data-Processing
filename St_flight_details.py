import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

#st.set_page_config(layout="wide")
flight_ID = int(st.query_params["Index"])

# Loading and preprocessing dataset
flight_log = pd.read_csv("Flight Log.csv")

flight_log = flight_log.rename(columns={"ID": "Field ID"})

flight_log['Index'] = range(1, len(flight_log) + 1)

flight_log.set_index("Index")

flight_details = flight_log.iloc[flight_ID]

title_col_1, title_col_2 = st.columns([0.9,0.1])
with title_col_1:
    st.markdown(f"""
    # Nr {flight_details["Index"]}: &nbsp;{flight_details["Flight Date"]} &nbsp; {flight_details["Field ID"]}&nbsp; {flight_details["Flight Start"]} - {flight_details["Flight End"]}""")

with title_col_2:
    st.text('')
    st.text('')
    edit_mode = st.checkbox("✍")

body_column_1, body_column_2 = st.columns(2)
body_column_3, body_column_4 = st.columns(2)

body_column_1_content = ["Step 1 Quality Check", "Quality checked by", "Workable Data", "Ready for next step (step 2 and 3)", "Ready for next step - person",
                         "Step 2 processing", "Step 3 Image Stitching", "Processed by", "QGIS", "QGIS person"]

body_column_2_content = ["Route type", "Image type", "Drone Model", "Drone type", "Camera Angle", "Flight Speed", "Flight Height", "Side Overlap", "Front Overlap", "Wind (m/s)"]

body_column_3_content = ["Project", "Location"]

with body_column_1:
    flight_details_col_1 = flight_details[body_column_1_content]
    st.table(flight_details_col_1)

with body_column_2:
    flight_details_col_2 = flight_details[body_column_2_content]
    st.table(flight_details_col_2)

with body_column_3:
    flight_details_col_3 = flight_details[body_column_3_content]
    st.table(flight_details_col_3)
