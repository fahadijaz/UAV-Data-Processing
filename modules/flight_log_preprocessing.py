import pandas as pd
from datetime import datetime, time
import re

def preprocessing():
    # Loading and preprocessing datasets
    #df_flight_log = pd.read_csv("P:\\PhenoCrop\\Test_Folder\\Test_SINDRE\\Git_repo\\UAV-Data-Processing - Copy (24.07.2024)\\Flight Log.csv")
    df_flight_log = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_log.csv")
    df_flight_routes = pd.read_csv("P:\\PhenoCrop\\0_csv\\flight_routes.csv")
    df_fields = pd.read_csv("P:\\PhenoCrop\\0_csv\\fields.csv")
    df_processing_status = pd.read_csv("P:\\PhenoCrop\\0_csv\\processing_status.csv")

    # Fixing the date formatting
    df_flight_log['date'] = pd.to_datetime(df_flight_log['date'], format='%Y%m%d').dt.date

    # Function to convert HHMMSS to datetime.time
    def convert_to_time(time_str):
        time_str = str(time_str).zfill(6) # Fixes the fact that sometimes, the start_time in the csv only has 5 digits.
        # Ensure the string is of the correct length and format
        if len(time_str) == 6:
            hours = int(time_str[:2])
            minutes = int(time_str[2:4])
            seconds = int(time_str[4:])
            return time(hour=hours, minute=minutes, second=seconds)
        else:
            print(time_str)
            raise ValueError("Time string must be in HHMMSS format")
    
    # Fixing the time formatting by applying the function
    df_flight_log['start_time'] = df_flight_log['start_time'].apply(convert_to_time)
    df_flight_log['end_time'] = df_flight_log['end_time'].apply(convert_to_time)
    

    # Merging dataframes
    df_merged_flight_log_flight_routes = pd.merge(df_flight_log, df_flight_routes, left_on='flight_name', right_on='FlightRoute')
    df_merged_flight_log_flight_routes_fields = pd.merge(df_merged_flight_log_flight_routes, df_fields, left_on='BaseName', right_on='Field ID')
    df_flight_log_merged = pd.merge(df_merged_flight_log_flight_routes_fields, df_processing_status, left_on='output_path', right_on='flight_output_path', how='left')

    
    # Function to extract the image type keyword from a cell
    def extract_image_type_keyword(cell):
        keywords = ['phantom-MS', 'MS', '3D']
        for keyword in keywords:
            if keyword in cell:
                return keyword
        return None

    # Applying the function to the 'type' column to create a new column with the extracted image type keywords
    df_flight_log_merged['image_type_keyword'] = df_flight_log_merged['type'].apply(extract_image_type_keyword)

    # Removing rows which have are part of the same flight (e.g. if a 3D flight have both a horizontal row and a vertical row, then I am removing the vertical)
    df_flight_log_merged_unique = df_flight_log_merged.drop_duplicates(subset='output_path', keep='first')


    return df_flight_log, df_flight_routes, df_fields, df_flight_log_merged_unique, df_processing_status

def import_log_file(log_file_path):
    # Define the regular expression pattern to extract components from each log entry
    log_pattern = re.compile(r'\[(?P<Timestamp>[^\]]+)\]\[ (?P<RAM>[^\]]+)\]\[ (?P<CPU>[^\]]+)\]\[(?P<LogLevel>[^\]]+)\]: (?P<Message>.*)')

    def parse_log_line(line):
        """Parse a single line of the log file and return a dictionary of extracted fields."""
        match = log_pattern.match(line)
        if match:
            return match.groupdict()
        return {}

    # Initialize a list to store parsed data
    data = []

    # Read and parse the log file line by line
    with open(log_file_path, 'r') as file:
        for line in file:
            parsed_line = parse_log_line(line)
            if parsed_line:
                data.append(parsed_line)

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data)

    # Convert the 'Timestamp' column to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y.%m.%d %H:%M:%S')
