import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# Loading and preprocessing dataset
flight_log = pd.read_csv("Flight Log.csv")

flight_log = flight_log.rename(columns={"ID": "Field ID"})

flight_log['Index'] = range(1, len(flight_log) + 1)

flight_log_selection = flight_log.copy()

# Fixing the date formatting
flight_log_selection["Flight Date"] = pd.to_datetime(flight_log_selection["Flight Date"] + "-2024", format="%d-%b-%Y").dt.date


# Options for input fields
field_IDs = ("PHENO", "PROTVOLL", "DIVERSITY", "FRONTIERS", "PILOT", "E166", "SØRÅS", "HIGHGRASS", "FABA")
route_types = ("3D", "MS")
drone_pilots = ("Fahad", "Isak", "Sindre")

# Creating input fields
input_field = st.selectbox("Field ID", field_IDs, index=None, placeholder="Field ID", label_visibility="collapsed")
input_date_start = st.date_input("Date from")
input_date_end = st.date_input("Date to")
input_type = st.selectbox("Route Type", route_types, index=None, placeholder="Route Type", label_visibility="collapsed")
input_pilot = st.selectbox("Drone Pilot", drone_pilots, index=None, placeholder="Drone Pilot", label_visibility="collapsed")

# Storing the user inputs in a dictionary
inputs_dict = {"Field ID": input_field, "Flight Date": [input_date_start, input_date_end], 
                "Route type": input_type, "Drone Pilot": input_pilot}

# Changing the dataset flight_log_selection in accordance with user inputs
for input_name in inputs_dict:
    input = inputs_dict[input_name]
    if input != None:
        if type(input) is not list:
        #if input != None & input != input_date_start & input != input_date_end:
            flight_log_selection = flight_log_selection[flight_log_selection[input_name] == input]

#st.write(flight_log_selection[["Field ID", "Flight Date", "Route type", "Drone Pilot"]], escape=False, unsafe_allow_html=True)


# Displaying the selected drone flights
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
.flight_log_header {
    background-color: rgb(250, 250, 250, 0.05);
}
.flight_log_header_cell {
    padding: 0.5rem;
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

html_content += """<table class='flight_log_table' border=1><tr class="flight_log_header"><th></th>"""
for name in flight_log_selection[["Field ID", "Flight Date", "Route type", "Drone Pilot"]].columns:
    html_content += f"""
        <td class="flight_log_header_cell">{name}</th>
    """

html_content += """</tr>"""


for index, row in flight_log_selection[["Index", "Field ID", "Flight Date", "Route type", "Drone Pilot"]].iterrows():
    html_content += f"""
        <tr class="flight_log_entry">
            <td class="flight_log_link_cell"><a href="http://localhost:8502?Index={row['Index']}" target="_blank"><img src="https://cdn-icons-png.flaticon.com/128/3388/3388930.png"></a></td>
            <td class="flight_log_cell">{row['Field ID']}</td>
            <td class="flight_log_cell">{row['Flight Date']}</td>
            <td class="flight_log_cell">{row['Route type']}</td>
            <td class="flight_log_cell">{row['Drone Pilot']}</td>
        </tr>
        """

html_content += "</table>"
components.html(html_content, height=600, scrolling=True)
#st.markdown(html_content, unsafe_allow_html=True)
