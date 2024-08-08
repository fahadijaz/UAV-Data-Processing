import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from modules.flight_log_preprocessing import preprocessing
import datetime

df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()

#df_flight_log_merged

flight_log_selection = df_flight_log_merged.copy()

# Options for input fields
excluded_field_IDs = ["Proteinbar NAPE", "GENE2BREAD", "High Grass", "Faba Bean"]
field_IDs = [value for value in df_fields["LongName"] if value not in excluded_field_IDs]
route_types = ("3D", "MS", "phantom-MS")
drone_pilots = ("Fahad", "Isak", "Sindre")

# Creating input fields
input_col_1, input_col_2, input_col_3 = st.columns(3)
with input_col_1:
    input_field = st.selectbox("Field", field_IDs, index=None, placeholder="Field", label_visibility="collapsed")
with input_col_2:
    input_type = st.selectbox("Route Type", route_types, index=None, placeholder="Route Type", label_visibility="collapsed")
with input_col_3:
    input_pilot = st.selectbox("Drone Pilot", drone_pilots, index=None, placeholder="Drone Pilot", label_visibility="collapsed")
date_col_1, date_col_2 = st.columns([0.5,0.5])
with date_col_1:
    input_date_start = st.date_input("Date from", datetime.date(datetime.datetime.now().year, 1, 1))
with date_col_2:
    input_date_end = st.date_input("Date to")

# Storing the user inputs in a dictionary
inputs_dict = {"LongName": input_field, "date": [input_date_start, input_date_end], 
                "image_type_keyword": input_type, "drone_pilot": input_pilot}

# Changing the dataset flight_log_selection in accordance with user inputs
for input_name in inputs_dict:
    input = inputs_dict[input_name]
    if input != None:
        if type(input) is not list:
        #if input != None & input != input_date_start & input != input_date_end:
            flight_log_selection = flight_log_selection[flight_log_selection[input_name] == input]
        else:
            flight_log_selection = flight_log_selection[(flight_log_selection['date'] >= input[0]) & (flight_log_selection['date'] <= input[1])]

#st.write(flight_log_selection[["Field ID", "date", "Route type", "Drone Pilot"]], escape=False, unsafe_allow_html=True)


# Displaying the selected drone flights
def display_flight_table(flight_log_selection):
    css = """
    <style>
    :root {
        --scrollbar-thumb: #888;
        --scrollbar-thumb-hover: #555;
    }
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-thumb {
        background-color: var(--scrollbar-thumb);
        border-radius: 6px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background-color: var(--scrollbar-thumb-hover);
    }

    .flight_log_table {
        border: 1px solid rgb(250, 250, 250, 0.1);
        width: 100%;
        color: white;
        font-family: "Source Sans Pro", sans-serif;
        font-weight: 400;
        line-height: 1.6;
        text-size-adjust: 100%;
        font-size: 14px;
        border-collapse: collapse;
        border-radius: 0.5rem;
    }
    .flight_log_header_1 {
        background-color: rgb(26, 29, 34);
    }
    .flight_log_header_2 {
        background-color: rgb(26, 29, 34);
    }
    .flight_log_header_cell {
        padding: 0.5rem;
        text-align: left;
    }

    /* Make the table header sticky */
    .flight_log_header_2 {
        position: sticky;
        top: 0;
        z-index: 2; /* Ensure the header stays above the table rows */
    }

    .sharp-left-border {
        border-left: 3px solid rgb(250, 250, 250, 0.1); /* Adjust the width and color as needed */
    }
    .flight_log_entry {
    }
    .flight_log_cell {
        padding: 0.5rem;
    }
    .flight_log_link_cell {
    }
    .flight_log_link_cell img {
        height: 1.3em;
        filter: invert(0.5);
    }
    </style>
    """

    html_content = css
    html_content += """
        <table class='flight_log_table' border=1>
            <tr class="flight_log_header_1">
                <th colspan="5"></th>
                <th colspan="7" class="flight_log_header_cell sharp-left-border">&nbsp;Processed</th>
            </tr>
            <tr class="flight_log_header_2"><th></th>"""
    for name in ["Field", "Date", "Image Type", "Drone Pilot", "DSM", "Blue", "Green", "NDVI", "NIR", "Red Edge", "Red"]:
        html_content += f"""
                <th class="flight_log_header_cell"""
        if name == "DSM":
            html_content += " sharp-left-border"
        html_content += f"""
                ">{name}</th>
        """

    html_content += """</tr>"""


    for index, row in flight_log_selection.iterrows():
        dsm_exists = 1 if row['DSM_Path'] else 0
        html_content += f"""
            <tr class="flight_log_entry">
                <td class="flight_log_link_cell"><a href="http://localhost:8502?Index={row['flight_ID']}" target="_blank"><img src="https://cdn-icons-png.flaticon.com/128/3388/3388930.png"></a></td>
                <td class="flight_log_cell">{row['LongName']}</td>
                <td class="flight_log_cell">{row['date']}</td>
                <td class="flight_log_cell">{row['image_type_keyword']}</td>
                <td class="flight_log_cell">{row['drone_pilot']}</td>
                <td class="flight_log_cell sharp-left-border">{int(dsm_exists)}</td>
                <td class="flight_log_cell">{int(row['Indice_blue'])}</td>
                <td class="flight_log_cell">{int(row['Indice_green'])}</td>
                <td class="flight_log_cell">{int(row['Indice_ndvi'])}</td>
                <td class="flight_log_cell">{int(row['Indice_nir'])}</td>
                <td class="flight_log_cell">{int(row['Indice_red_edge'])}</td>
                <td class="flight_log_cell">{int(row['Indice_red'])}</td>
            </tr>
            """

    html_content += "</table>"
    components.html(html_content, height=700, scrolling=True)
    #st.markdown(html_content, unsafe_allow_html=True)

display_flight_table(flight_log_selection)