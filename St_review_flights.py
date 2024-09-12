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
    input_type = st.selectbox("Flight Type", route_types, index=None, placeholder="Flight Type", label_visibility="collapsed")
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


# Goes through the flight_log and returns a dictionary of percentages for each column
def flight_log_percentages(flight_log_selection, columns_to_calculate):
    value_percentages = {}
    for column in columns_to_calculate:
        # Calculate the total number of entries in the column
        total_entries = len(flight_log_selection[column])
        # Calculate the percentage of each unique value
        percentages = flight_log_selection[column].value_counts(normalize=True) * 100
        
        # Store the percentages in the dictionary
        value_percentages[column] = percentages
    
    return value_percentages

flight_log_percentages_columns = ["LongName", "image_type_keyword", "drone_pilot", "processed"]
flight_log_percentages_columns_names = ["Field", "Image Type", "Drone Pilot", "Processed"]

column_percentages = flight_log_percentages(flight_log_selection, flight_log_percentages_columns)

#st.write(column_percentages)

# Displaying the selected drone flights
def display_flight_table(flight_log_selection):
    css = """
    <style>
    :root {
        --scrollbar-thumb: #888;
        --scrollbar-thumb-hover: #555;
        --flight-entry-color-green: rgba(0, 255, 0, 0.3);
        --flight-entry-color-blue: rgba(0, 0, 255, 0.1);
        --flight-entry-color-grey: rgba(128, 128, 128, 0.3);
        --flight-entry-color-yellow: rgba(255, 255, 0, 0.3);
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
        top: -1px;
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
    .extra_info {
        display: none; /* Hide by default */
    }
    /* Container for the button to position it absolutely within the <th> */
    .button-container {
        position: absolute; /* Position it relative to the <th> */
        left: 0; /* Align to the left edge */
        top: 50%; /* Center vertically */
        transform: translateY(-50%); /* Adjust vertical alignment */
    }

    /* Make sure the <th> has a position relative to contain the absolute positioning */
    .flight_log_header_cell_wide {
        position: relative; /* Create a positioning context for child elements */
    }

    .flight_log_entry_processed_notongoing {
        background-color: var(--flight-entry-color-green);
    }
    .flight_log_entry_processed_ongoing {
        background: repeating-linear-gradient(
            45deg,                                  /* Angle of the stripes */
            var(--flight-entry-color-green),                   /* Green with 50% opacity */
            var(--flight-entry-color-green) 5px,              /* Green stripe ends at 10px */
            var(--flight-entry-color-blue) 5px,              /* Blue starts at 10px */
            var(--flight-entry-color-blue) 10px               /* Blue stripe ends at 20px */
        );
    }
    .flight_log_entry_notprocessed_ongoing {
        background-color: var(--flight-entry-color-blue);
    }
    .flight_log_entry_notprocessed_notongoing {
        background-color: var(--flight-entry-color-yellow)
    }
    .flight_log_entry_unknown_notongoing {
        background-color: var(--flight-entry-color-grey);
    }
    .flight_log_entry_unknown_ongoing {
        background: repeating-linear-gradient(
            45deg,                                  /* Angle of the stripes */
            var(--flight-entry-color-grey),   /* Grey with 50% opacity */
            var(--flight-entry-color-grey) 5px, /* Grey stripe ends at 5px */
            var(--flight-entry-color-blue) 5px,     /* Blue starts at 5px */
            var(--flight-entry-color-blue) 10px     /* Blue stripe ends at 10px */
        );
    }
    </style>
    """

    html_content = css
    html_content += f"""
        <table class='flight_log_table' border=1>
            <tr class="flight_log_header_2"><th>
                <!-- Button to toggle extra info -->
                <div class="button-container">
                    <!-- <button id="toggle_extra_info">Show</button> -->
                </div>
            </th>"""
    for name in ["Field", "Date", "Image Type", "Drone Pilot", "Processing status", "Coordinates correct?"]:
        html_content += f"""
                <th class="flight_log_header_cell">{name}"""
        
        if name in flight_log_percentages_columns_names:
            index_of_column = flight_log_percentages_columns_names.index(name)
            column_name_in_df = flight_log_percentages_columns[index_of_column]
            if 1 in column_percentages[column_name_in_df].index:
                percentage = round(column_percentages[column_name_in_df][1])
                html_content += f"""
                        <span class="extra_info"> ({percentage}%)</span>
                """
        html_content += f"</th>"

    html_content += """</tr>"""


    for index, row in flight_log_selection.iterrows():
        this_processed = int(row['processed']) if not pd.isna(row['processed']) else '?'
        this_ongoing = row['ongoing']

        # Setting processing status based on the combination of processing status and ongoing status
        this_processing_status = ""
        this_processing_status_msg = ""
        if this_processed == 1 and this_ongoing == 0:
            this_processing_status = "processed_notongoing"
            this_processing_status_msg = "Fully processed"
        if this_processed == 1 and this_ongoing == 1:
            this_processing_status = "processed_ongoing"
            this_processing_status_msg = "Fully processed & processing"
        if this_processed == 0 and this_ongoing == 1:
            this_processing_status = "notprocessed_ongoing"
            this_processing_status_msg = "Processing"
        if this_processed == 0 and this_ongoing == 0:
            this_processing_status = "notprocessed_notongoing"
            this_processing_status_msg = "Neither processed nor processing"
        if this_processed == "?" and pd.isna(this_ongoing):
            this_processing_status = "unknown_notongoing"
            this_processing_status_msg = "Unknown processing status"
        if this_processed == "?" and this_ongoing == 1:
            this_processing_status = "unknown_ongoing"
            this_processing_status_msg = "Unknown processed status, but currently processing"
        
        # Printing row for this flight
        html_content += f"""
            <tr class='flight_log_entry flight_log_entry_{this_processing_status}'>
                <td class="flight_log_link_cell"><a href="http://localhost:8502?Index={row['flight_ID']}" target="_blank"><img src="https://cdn-icons-png.flaticon.com/128/3388/3388930.png"></a></td>
                <td class="flight_log_cell">{row['LongName']}</td>
                <td class="flight_log_cell">{row['date']}</td>
                <td class="flight_log_cell">{row['image_type_keyword']}</td>
                <td class="flight_log_cell">{row['drone_pilot']}</td>
                <!-- <td class="flight_log_cell">{this_processed}</td> -->
                <!-- <td class="flight_log_cell">{this_ongoing}</td> -->
                <td class="flight_log_cell">{this_processing_status_msg}</td>
                <td class="flight_log_cell">{row['coordinates_correct']}</td>
            </tr>
            """

    html_content += "</table>"
    html_content += """
        <script>
            // JavaScript to toggle visibility of extra_info spans
            document.addEventListener('DOMContentLoaded', function() {
                var button = document.getElementById('toggle_extra_info');
                var extraInfoElements = document.querySelectorAll('.extra_info');
                var isVisible = false; // Track visibility state

                button.addEventListener('click', function() {
                    isVisible = !isVisible; // Toggle the state
                    extraInfoElements.forEach(function(element) {
                        element.style.display = isVisible ? 'inline' : 'none'; // Toggle visibility
                    });
                });
            });
        </script>
        """
    components.html(html_content, height=700, scrolling=True)
    #st.markdown(html_content, unsafe_allow_html=True)

display_flight_table(flight_log_selection)

processed_percentage = column_percentages['processed'][1]
processed_count = round(len(flight_log_selection)*processed_percentage/100)
ongoing_count = flight_log_selection['ongoing'].sum()
bottom_text = f"Showing {len(flight_log_selection)} flights.&nbsp; Of which {processed_count} ({round(processed_percentage)}%) are fully processed and {round(ongoing_count)} are ongoing."
st.write(bottom_text)