import subprocess
import os
import sys
import glob


# Function to open the folder in the file explorer
def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


# Function to find the tif files in a given folder
def find_tif_file(folder_path):
    tif_files = []
    tif_files.extend(glob.glob(os.path.join(folder_path, "**", "*.tif"), recursive=True))

    if tif_files == []:
        tif_files = [""]
    return tif_files


# Function to find the tif files in a given folder's subfolders (but not their subfolders)
def find_tif_files_in_subfolders(folder_path):
    tif_files = []
    tif_folders = []
    if os.path.isdir(folder_path):
        tif_folders = os.listdir(folder_path)
        # List all items in the given folder_path
        for item in os.listdir(folder_path):
            # Construct full path
            subdir_path = rf"{folder_path}\{item}"

            # Check if the item is a directory
            if os.path.isdir(subdir_path):
                # Look for .tif files in the current subdirectory
                found_tifs = glob.glob(os.path.join(subdir_path, "*.tif"))
                tif_files.extend(found_tifs)

    # Return list of .tif files found, or [""] if none were found
    if tif_files == []:
        tif_files = [""]
    return tif_files, tif_folders
