import streamlit as st
from filetransfer import FileTransfer
import subprocess
import os

st.set_page_config(layout="wide")

DB_PATH = "database/drone_data.db"

#############################################
# This section is responsible for detecting SD cards on different platforms
import os
import platform
import string
import ctypes
import streamlit as st

def is_removable_drive_windows(drive_letter):
    """
    Checks whether the specified drive is a removable drive (e.g., SD card or USB) on Windows.

    Args:
        drive_letter (str): Drive letter, e.g., 'E'

    Returns:
        bool: True if the drive is removable, False otherwise.
    """
    DRIVE_REMOVABLE = 2
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive_letter}:/")
    return drive_type == DRIVE_REMOVABLE


def find_sd_cards_windows(dcim_folder="DCIM"):
    """
    Detects SD cards on Windows systems by scanning for removable drives containing the DCIM folder.

    Args:
        dcim_folder (str): The folder to look for on the SD card (default: 'DCIM').

    Returns:
        list: List of valid SD card paths containing the target folder.
    """
    sd_cards = []
    for drive_letter in string.ascii_uppercase:
        drive_path = f"{drive_letter}:/"
        target_path = os.path.join(drive_path, dcim_folder)

        try:
            if is_removable_drive_windows(drive_letter) and os.path.exists(target_path):
                sd_cards.append(target_path)
        except Exception as e:
            print(f"Skipping {drive_letter}: {e}")
    return sd_cards


def find_sd_cards_unix(dcim_folder="DCIM"):
    """
    Detects SD cards on macOS/Linux systems by scanning mounted volumes.

    Args:
        dcim_folder (str): Folder to look for on the SD card (default: 'DCIM').

    Returns:
        list: List of valid SD card paths containing the target folder.
    """
    mount_points = ["/media", "/Volumes", "/mnt"]
    sd_cards = []

    for base_path in mount_points:
        if os.path.exists(base_path):
            for device in os.listdir(base_path):
                device_path = os.path.join(base_path, device)
                target_path = os.path.join(device_path, dcim_folder)
                if os.path.isdir(target_path):
                    sd_cards.append(target_path)

    return sd_cards

def look_for_sd_cards_in_streamlit(dcim_folder="DCIM"):
    """
    Streamlit-compatible SD card scanner with fallback to manual folder input.

    Args:
        dcim_folder (str): Subfolder to verify presence of an SD card (typically 'DCIM').

    Returns:
        list: A list of valid SD card paths, possibly manually selected via Streamlit.
    """

    system_platform = platform.system()
    detected_cards = []

    if system_platform == "Windows":
        detected_cards = find_sd_cards_windows(dcim_folder)
    elif system_platform in ("Linux", "Darwin"):
        detected_cards = find_sd_cards_unix(dcim_folder)

    # Streamlit fallback to manual path input
    if not detected_cards:
        st.warning("No SD cards with DCIM folder found. Please select a folder manually.")
        manual_path = st.text_input("Enter the path to the SD card manually:")
        if manual_path and os.path.isdir(os.path.join(manual_path, dcim_folder)):
            detected_cards.append(os.path.join(manual_path, dcim_folder))

    return detected_cards


##############################################
# This function loads file transfers from detected SD cards and initializes the FileTransfer objects.
# Note: The paths for output, flight routes, and flight logs are set dynamically based on the project info.

# ==============================================================================
# ROUTE INFO RETRIEVAL - FULL PROJECT MAPPING
# ==============================================================================

def get_flight_route_info() -> dict:
    """
    Retrieves all flight route and flight log information organized by project (BasePath).

    Returns:
        dict[str, dict]: A dictionary structured as:
            {
                "project_name_or_basepath": {
                    "output_path": str,
                    "flight_routes": list[dict],
                    "flight_log": list[dict]
                },
                ...
            }

    Notes:
        - Uses `BasePath` as the primary key to group related routes and logs.
        - If no matching logs exist for a project, the `flight_log` list will be empty.
    """
    conn = sqlite3.connect(DB_PATH)  # Use the correct path to your database
    conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
    cur = conn.cursor()

    # Fetch all routes
    cur.execute("SELECT * FROM flight_routes")
    route_rows = cur.fetchall()

    # Organize routes by BasePath
    project_data = {}
    for row in route_rows:
        route = dict(row)
        project = route.get("BasePath")

        if project not in project_data:
            project_data[project] = {
                "output_path": project,
                "flight_routes": [],
                "flight_log": []
            }
        project_data[project]["flight_routes"].append(route)

    # Fetch all logs
    cur.execute("SELECT * FROM flight_log")
    log_rows = cur.fetchall()

    for log in log_rows:
        log_entry = dict(log)
        log_path = log_entry.get("output_path")
        if log_path in project_data:
            project_data[log_path]["flight_log"].append(log_entry)

    conn.close()
    return project_data


        
        
def load_file_transfers():
    """
    Load file transfers by initializing FileTransfer objects from detected SD cards.
    Flight routes, logs, and output paths are determined dynamically based on project info.

    Returns:
        list: List of FileTransfer objects.
    """
    st.session_state.current_index = 0
    st.session_state.file_transfers = []
    st.session_state.edit_mode = False
    st.session_state.ready_to_move = False
    st.session_state.data_loaded = False

    # Detect SD card paths
    sd_card_paths = look_for_sd_cards_in_streamlit()

    # Get flight route data (project, output_path, logs, etc.)
    flight_route_info = get_flight_route_info()  # returns dict: {project: {"output_path": ..., "flight_routes": ..., "flight_log": ...}}

    project = st.selectbox("Select Project", list(flight_route_info.keys()))
    selected_project = flight_route_info.get(project, {})

    output_path = selected_project.get("output_path")
    flight_routes = selected_project.get("flight_routes")
    flight_log = selected_project.get("flight_log")

    if not all([output_path, flight_routes, flight_log]):
        st.error("Missing required path information for the selected project.")
        return []

    # Create FileTransfer objects for each detected SD card
    obj_list = [
        FileTransfer(
            input_path=path,
            output_path=output_path,
            data_overview_file=flight_routes,
            flight_log=flight_log
        ) for path in sd_card_paths
    ]

    for ft in obj_list:
        ft.get_information()
        ft.reflectance_logic_with_timestamps()
        ft.detect_and_handle_new_routes()
        ft.match()

    return obj_list





def display_file_transfers():
    """
    Displays the current FileTransfer object from the list with navigation and editing options.
    """
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)

        if st.button('Edit this SD Card'):
            st.session_state.edit_mode = True
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.current_index < (len(st.session_state.file_transfers) - 1):
                if st.button('Next SD Card'):
                    next_sd_card()
                    st.rerun()
        with col2:
            if st.session_state.current_index > 0:
                if st.button('Previous SD Card'):
                    prev_sd_card()
                    st.rerun()


def prev_sd_card():
    st.session_state.current_index -= 1


def next_sd_card():
    st.session_state.current_index += 1
    st.session_state.edit_mode = False


def print_display(ft):
    """
    Display the input and output paths for all flights on the current SD card.
    """
    st.text(f"SD Card {st.session_state.current_index + 1} - Path: {ft.input_path}")
    col1, col2 = st.columns([1, 2])
    for i, flight in enumerate(ft.flights_folders):
        with col1:
            st.text(f"{i}. from: {flight['dir_name']}")
        with col2:
            st.text(f"to: {flight['output_path']}")


def edit_current_obj():
    """
    Provides UI for editing actions like Move, Trash, Duplicate, Skyline, or Continue.
    """
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 6])

        if col1.button("Move"):
            st.session_state.edit_mode = False
            st.session_state.move_mode = True
            st.rerun()
        if col2.button("Trash"):
            st.session_state.edit_mode = False
            st.session_state.trash_mode = True
            st.rerun()
        if col3.button("Duplicate"):
            st.session_state.edit_mode = False
            st.session_state.dupe_mode = True
            st.rerun()
        if col4.button("_SKYLINE"):
            st.session_state.edit_mode = False
            st.session_state.skyline_mode = True
            st.rerun()
        if col5.button("Continue"):
            st.session_state.edit_mode = False
            st.rerun()


def move():
    """
    Move files from one index to another.
    """
    ft = st.session_state.file_transfers[st.session_state.current_index]
    print_display(ft)
    flight_index = st.text_input('From:')
    new_path_index = st.text_input('To:')
    if st.button('Confirm') and flight_index and new_path_index:
        ft._move_path(streamlit_mode=True, flight_index=int(flight_index), new_path_index=int(new_path_index))
        st.session_state.edit_mode = True
        st.session_state.move_mode = False
        st.rerun()


def trash():
    ft = st.session_state.file_transfers[st.session_state.current_index]
    print_display(ft)
    flight_index = st.text_input('Flight to trash:')
    if st.button('Confirm') and flight_index:
        ft._trash_path(streamlit_mode=True, flight_index=int(flight_index))
        st.session_state.edit_mode = True
        st.session_state.trash_mode = False
        st.rerun()


def dupe():
    ft = st.session_state.file_transfers[st.session_state.current_index]
    print_display(ft)
    flight_index = st.text_input('From:')
    new_path_index = st.text_input('To:')
    if st.button('Confirm') and flight_index and new_path_index:
        ft._duplicate_path(streamlit_mode=True, flight_index=int(flight_index), new_path_index=int(new_path_index))
        st.session_state.edit_mode = True
        st.session_state.dupe_mode = False
        st.rerun()


def skyline():
    ft = st.session_state.file_transfers[st.session_state.current_index]
    print_display(ft)
    flight_index = st.text_input('Flight move to skyline:')
    if st.button('Confirm') and flight_index:
        ft._skyline_path(streamlit_mode=True, flight_index=int(flight_index))
        st.session_state.edit_mode = True
        st.session_state.skyline_mode = False
        st.rerun()


def update_and_whipe():
    if st.session_state.file_transfers:
        for ft in st.session_state.file_transfers:
            ft.update_main_csv()
            ft._close_and_wipe_sd_cards()

        st.session_state.file_transfers = []
        st.session_state.update_and_whipe = False
        st.rerun()
    else:
        st.write('No file transfers found or incorrect state.')


##############################################
# This section is responsible for managing pilots and drone models
# check terminal for username ? 
import sqlite3

def get_pilots():
    """
    Retrieves a list of pilot names from the SQLite database.

    Returns:
        list: A list of pilot names (str).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM pilots")
    results = [row[0] for row in cur.fetchall()]
    conn.close()
    return results

def get_drones():
    """
    Retrieves a list of drone model identifiers from the SQLite database.

    Returns:
        list: A list of drone models (str).
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT model FROM drones")
    results = [row[0] for row in cur.fetchall()]
    conn.close()
    return results


import streamlit as st

def initialize_session():
    """
    Initializes all required Streamlit session state variables
    with default values if they are not already set.
    """
    st.session_state.setdefault("data_loaded", False)
    st.session_state.setdefault("ready_to_move", False)
    st.session_state.setdefault("edit_mode", False)
    st.session_state.setdefault("move_mode", False)
    st.session_state.setdefault("dupe_mode", False)
    st.session_state.setdefault("trash_mode", False)
    st.session_state.setdefault("skyline_mode", False)
    st.session_state.setdefault("update_and_whipe", False)
    st.session_state.setdefault("current_index", 0)

def render_sidebar():
    """
    Renders the sidebar UI for drone pilot and model selection.
    Data is fetched from an external SQLite database.
    """
    st.header("Drone Details")

    # Retrieve data from the database
    pilots = ['Choose a pilot'] + get_pilots()
    drones = ['Choose a drone'] + get_drones()

    # Selection widgets
    st.session_state.drone_pilot = st.selectbox("Select Drone Pilot", pilots, index=0)
    st.session_state.drone_model = st.selectbox("Select Drone Model", drones, index=0)

def handle_file_transfer():
    """
    Handles the 'Load SD Cards' button.
    Loads file transfer data and updates session state flags.
    """
    if st.button("Load SD Cards"):
        st.session_state.file_transfers = load_file_transfers()
        st.session_state.data_loaded = True
        st.session_state.ready_to_move = False

def handle_modes():
    """
    Executes appropriate mode behavior based on session state.
    Assumes all mode functions (skyline, trash, etc.) are defined externally.
    """
    if st.session_state.update_and_whipe:
        update_and_whipe()
    elif st.session_state.skyline_mode:
        skyline()
    elif st.session_state.trash_mode:
        trash()
    elif st.session_state.dupe_mode:
        dupe()
    elif st.session_state.move_mode:
        move()
    elif st.session_state.edit_mode:
        edit_current_obj()
    else:
        display_file_transfers()

def handle_confirm_and_move():
    """
    Handles logic related to final confirmation and moving files.
    Displays confirmation button and performs file movement if confirmed.
    """
    if (
        st.session_state.file_transfers
        and not st.session_state.ready_to_move
        and st.session_state.current_index == len(st.session_state.file_transfers) - 1
        and not st.session_state.edit_mode
    ):
        if st.button("Confirm"):
            st.session_state.ready_to_move = True
            st.success("Ready to move files. Please proceed with the final operation.")

    # Executes file move operations
    if st.session_state.ready_to_move and st.button("Move All Files"):
        for ft in st.session_state.file_transfers:
            ft.move_files_to_output(streamlit_mode=True)
            ft._save_flight_log(
                streamlit_mode=True,
                drone_pilot=st.session_state.drone_pilot,
                drone=st.session_state.drone_model,
            )

        st.session_state.update_and_whipe = True
        st.success("Files moved successfully. Process completed.")

        if st.button("Update main log and Wipe SD Cards"):
            for ft in st.session_state.file_transfers:
                st.session_state.ready_to_move = False


def initialize_session_state(defaults: dict):
    """
    Initialize Streamlit session state variables with default values.

    Parameters:
        defaults (dict): A dictionary where keys are session state variable names
                         and values are their default values.
    """
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def main():
    """
    Entry point for the Streamlit app. Controls the high-level flow
    of UI rendering, file handling, and user interaction.
    """
    
    st.title("SD Card File Transfer Management")
    initialize_session()

    # Sidebar: Pilot & Drone Info
    with st.sidebar:
        render_sidebar()

    # Main control logic
    handle_file_transfer()

    if st.session_state.data_loaded:
        handle_modes()
        handle_confirm_and_move()

    # Define all required session state variables and their defaults
    default_session_state = {
        'file_transfers': [],
        'current_index': 0,
        'ready_to_move': False,
        'edit_mode': False,
        'data_loaded': False,
        'move_mode': False,
        'dupe_mode': False,
        'trash_mode': False,
        'skyline_mode': False,
        'update_and_whipe': False,
    }

    # Call the initializer early in your app
    initialize_session_state(default_session_state)

# Run the application
main()