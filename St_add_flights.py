import streamlit as st
from filetransfer import FileTransfer
import os

st.set_page_config(layout="wide")

def load_file_transfers():
    st.session_state.current_index = 0
    st.session_state.file_transfers = []
    st.session_state.edit_mode = False
    st.session_state.ready_to_move = False
    st.session_state.data_loaded = False

    output_path = "P:\\PhenoCrop\\1_flights"
    data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
    flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"
    sd_card_paths = ["G:/DCIM", "I:/DCIM", "D:/DCIM"]
    sd_card_paths = [path for path in sd_card_paths if os.path.exists(path)]
    obj_list = [FileTransfer(input_path=path, output_path=output_path, data_overview_file=data_file, flight_log=flight_log) for path in sd_card_paths]
    for ft in obj_list:
        ft.get_information()
        ft.reflectance_logic_with_timestamps()
        ft.detect_and_handle_new_routes()
        ft.match()
    return obj_list

# Initialize session state variables
if 'file_transfers' not in st.session_state:
    st.session_state.file_transfers = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'ready_to_move' not in st.session_state:
    st.session_state.ready_to_move = False
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

def display_file_transfers():
    if st.session_state.file_transfers:
            ft = st.session_state.file_transfers[st.session_state.current_index]
            st.text(f"SD Card {st.session_state.current_index + 1} - Path: {ft.input_path}")
            st.text(len(st.session_state.file_transfers))

            col1, col2 = st.columns([1, 2])  # Adjust the ratio as needed for your data
            for i, flight in enumerate(ft.flights_folders):
                with col1:
                    st.text(f"{i}. from: {flight['dir_name']}")
                with col2:
                    st.text(f"to: {flight['output_path']}")

            if st.button('Edit this SD Card'):
                st.session_state.edit_mode = True  # Toggle edit mode on
                st.experimental_rerun()

            if st.button('Next SD Card', on_click=lambda: next_sd_card()):
                st.rerun()

def next_sd_card():
    """Move to the next SD card in the list, if available."""
    if st.session_state.current_index < len(st.session_state.file_transfers) - 1:
        st.session_state.current_index += 1
        st.session_state.edit_mode = False  # Reset edit mode when moving to next card

def main():
    st.title("SD Card File Transfer Management")
    
    # Button to load SD cards
    if st.button("Load SD Cards"):
        st.session_state.file_transfers = load_file_transfers()
        st.session_state.data_loaded = True
        st.session_state.ready_to_move = False  # Reset the move flag

    if st.session_state.data_loaded:
        # Display all file transfers with an option to edit
        if st.session_state.file_transfers and not st.session_state.edit_mode:
            display_file_transfers()
        
        # Button to confirm all edits are done and ready to move files
        if st.session_state.file_transfers and not st.session_state.ready_to_move and st.session_state.current_index == (len(st.session_state.file_transfers)-1):
            if st.button("Confirm All Edits"):
                st.session_state.ready_to_move = True
                st.success("Ready to move files. Please proceed with the final operation.")
        
        # Option to move files after confirmation
        if st.session_state.ready_to_move:
            if st.button("Move All Files"): #### add check if session index == len( objs -1)!!!
                for ft in st.session_state.file_transfers:
                    ft.move_files_to_output()
                st.success("Files moved successfully. Process completed.")
                # Optionally reset the application or close operations
                st.session_state.file_transfers = []
                st.session_state.ready_to_move = False

if __name__ == "__main__":
    main()
