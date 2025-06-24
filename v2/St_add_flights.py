import streamlit as st
from filetransfer import FileTransfer
import subprocess
import os

st.set_page_config(layout="wide")

def look_for_sd_cards():
    sd_card_paths = ["D:/DCIM", "E:/DCIM", "F:/DCIM", "G:/DCIM", "I:/DCIM"]
    return [path for path in sd_card_paths if os.path.exists(path)]

def load_file_transfers():
    st.session_state.current_index = 0
    st.session_state.file_transfers = []
    st.session_state.edit_mode = False
    st.session_state.ready_to_move = False
    st.session_state.data_loaded = False

    output_path = "D:\\PhenoCrop\\1_flights"
    data_file = "D:\\PhenoCrop\\0_csv\\flight_routes.csv"
    flight_log = "D:\\PhenoCrop\\0_csv\\flight_log.csv"
    sd_card_paths = look_for_sd_cards()
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
if 'move_mode' not in st.session_state:
    st.session_state.move_mode = False
if 'dupe_mode' not in st.session_state:
    st.session_state.dupe_mode = False
if 'trash_mode' not in st.session_state:
    st.session_state.trash_mode = False
if 'skyline_mode' not in st.session_state:
    st.session_state.skyline_mode = False
if 'update_and_whipe' not in st.session_state:
    st.session_state.update_and_whipe = False


def display_file_transfers():
    if st.session_state.file_transfers:
            ft = st.session_state.file_transfers[st.session_state.current_index]

            #st.text(len(st.session_state.file_transfers))
            print_display(ft)
            if st.button('Edit this SD Card'):
                st.session_state.edit_mode = True  # Toggle edit mode on
                st.rerun()
            if st.session_state.current_index < (len(st.session_state.file_transfers)-1):
                if st.button('Next SD Card', on_click=lambda: next_sd_card()):
                    st.rerun()
            if st.session_state.current_index>0:
                if st.button('Previous SD Card', on_click=lambda: prev_sd_card()):
                    st.rerun()
def prev_sd_card():
    st.session_state.current_index -= 1
def next_sd_card():
    """Move to the next SD card in the list, if available."""
    if st.session_state.current_index < len(st.session_state.file_transfers) - 1:
        st.session_state.current_index += 1
        st.session_state.edit_mode = False  # Reset edit mode when moving to next card

def print_display(ft):
    st.text(f"SD Card {st.session_state.current_index + 1} - Path: {ft.input_path}")
    col1, col2 = st.columns([1, 2])  # Adjust the ratio as needed for your data
    for i, flight in enumerate(ft.flights_folders):
        with col1:
            st.text(f"{i}. from: {flight['dir_name']}")
        with col2:
            st.text(f"to: {flight['output_path']}")

def edit_current_obj():
    if st.session_state.file_transfers:
            ft = st.session_state.file_transfers[st.session_state.current_index]
            print_display(ft)
            col1, col2, col3, col4, col5 = st.columns([1,1,1,1,6])
            with col1:
                if st.button("Move"):
                    st.session_state.edit_mode = False
                    st.session_state.move_mode = True
                    st.rerun()
                
            with col2:
                if st.button("Trash"):
                    st.session_state.edit_mode = False
                    st.session_state.trash_mode = True
                    st.rerun()
            with col3:
                if st.button("Duplicate"):
                    st.session_state.edit_mode = False
                    st.session_state.dupe_mode = True
                    st.rerun()
    
            with col4:
                if st.button("_SKYLINE"):
                    st.session_state.edit_mode = False
                    st.session_state.skyline_mode = True
                    st.rerun()
            with col5:
                if st.button("continue"):
                    st.session_state.edit_mode = False
                    st.rerun()
def move():
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)
        col01, col02 = st.columns(2)
        with col01:
            flight_index = st.text_input('From:')
        with col02:
            new_path_index = st.text_input('To:')
        if st.button('confirm') and flight_index and new_path_index:
            ft._move_path(streamlit_mode=True, flight_index=int(flight_index),new_path_index=int(new_path_index))
            st.session_state.edit_mode = True
            st.session_state.move_mode = False
            st.rerun()


def trash():
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)
        
        
        flight_index = st.text_input('Flight to trash:')

        if st.button('confirm') and flight_index:
            ft._trash_path(streamlit_mode=True, flight_index=int(flight_index))
            st.session_state.edit_mode = True
            st.session_state.trash_mode = False
            st.rerun()
def dupe():
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)
        col01, col02 = st.columns(2)
        with col01:
            flight_index = st.text_input('From:')
        with col02:
            new_path_index = st.text_input('To:')
        if st.button('confirm') and flight_index and new_path_index:
            ft._duplicate_path(streamlit_mode=True, flight_index=int(flight_index),new_path_index=int(new_path_index))
            st.session_state.edit_mode = True
            st.session_state.dupe_mode = False
            st.rerun()

def skyline():
    if st.session_state.file_transfers:
        ft = st.session_state.file_transfers[st.session_state.current_index]
        print_display(ft)


        flight_index = st.text_input('Flight move to skyline:')

        if st.button('confirm') and flight_index:
            ft._skyline_path(streamlit_mode=True, flight_index=int(flight_index))
            st.session_state.edit_mode = True
            st.session_state.skyline_mode = False
            st.rerun()

def update_and_whipe():
    if st.session_state.file_transfers:
        
        ft = st.session_state.file_transfers[st.session_state.current_index]
        #st.text('prepping to updated')
        ft.update_main_csv()
        #st.text('updateded')
        for ft in st.session_state.file_transfers:
            #st.text('preppingto whipe')
            ft._close_and_wipe_sd_cards()
            #st.text('wiped')
        st.session_state.file_transfers = []
        st.session_state.update_and_whipe = False
        st.rerun()
    else:
        st.write('No file transfers found or incorrect state.')
        

# check terminal for username ? 
def main():
    st.title("SD Card File Transfer Management")
    with st.sidebar:
        
        st.header("Drone Details")
        st.session_state.drone_pilot = st.selectbox('Select Drone Pilot', ['choose a drone pilot', 'Mathias','Sindre', 'Isak', 'Fahad'], index=0)
        st.session_state.drone_model = st.selectbox('Select Drone Model', ['choose a drone','M3M-1', 'M3M-2', 'P4M-1', 'P4M-2', 'P4M-3'], index=0)

    # Button to load SD cards


    if st.button("Load SD Cards"):
        
        st.session_state.file_transfers = load_file_transfers()
        st.session_state.data_loaded = True
        st.session_state.ready_to_move = False  # Reset the move flag

    if st.session_state.data_loaded:
        # Display all file transfers with an option to edit
        if st.session_state.file_transfers and not st.session_state.edit_mode and not st.session_state.move_mode and not st.session_state.dupe_mode and not st.session_state.trash_mode and not st.session_state.skyline_mode and not st.session_state.update_and_whipe:
            display_file_transfers()

        if st.session_state.update_and_whipe:
            update_and_whipe()

        if st.session_state.skyline_mode:
            skyline()

        if st.session_state.trash_mode:
            trash()

        if st.session_state.dupe_mode:
            dupe()

        if st.session_state.move_mode:
            move()

        if st.session_state.edit_mode:
            edit_current_obj()
        # Button to confirm all edits are done and ready to move files
        if st.session_state.file_transfers and not st.session_state.ready_to_move and st.session_state.current_index == (len(st.session_state.file_transfers)-1) and not st.session_state.edit_mode:
            if st.button("Confirm"):
                st.session_state.ready_to_move = True
                st.success("Ready to move files. Please proceed with the final operation.")
        
        # Option to move files after confirmation
        if st.session_state.ready_to_move:
            if st.button("Move All Files"): #### add check if session index == len( objs -1)!!!
                for ft in st.session_state.file_transfers:
                    #st.text('simulating moving files and saving them')
                    ft.move_files_to_output(streamlit_mode=True)
                    ft._save_flight_log(streamlit_mode=True, drone_pilot=st.session_state.drone_pilot, drone=st.session_state.drone_model)
                    st.text('finished')
                    st.session_state.update_and_whipe = True
                    st.success("Files moved successfully. Process completed.")
 
                # Optionally reset the application or close operations
                
                if st.button('Update main log and Wipe SD Cards'):
                    for ft in st.session_state.file_transfers:
                        #st.text('whiping')
                        st.session_state.ready_to_move = False


    #st.write('Current State:')
    #st.json(st.session_state)
    # add route method, or add csv. some kind of add route system


main()
