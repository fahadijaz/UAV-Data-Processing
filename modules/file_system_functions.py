import subprocess
import os
import sys
import glob
import streamlit as st


# Function to open the folder in the file explorer
def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


def find_files_in_folder(folder_path, extension=None, recursive=False):
    """
    Retrieves a list of file paths in a specified folder, optionally filtered by file extension,
    and optionally including subdirectories.

    Parameters:
    - folder_path (str): The path of the folder to search for files.
    - extension (str, optional): The file extension to filter by (e.g., "txt" or "tif").
                                 If None, the function lists all files.
    - recursive (bool, optional): If True, includes files from all subdirectories within `folder_path`.
                                  Defaults to False (only lists files in the specified folder).

    Returns:
    - list of str: A list of file paths that match the specified extension in the folder.
                   If no matching files are found, returns a list containing an empty string.

    Example:
    >>> find_files_in_folder("/path/to/folder", "tif")
    ['/path/to/folder/file1.tif', '/path/to/folder/file2.tif']

    >>> find_files_in_folder("/path/to/folder", recursive=True)
    ['/path/to/folder/file1.tif', '/path/to/folder/subfolder/file2.txt', '/path/to/folder/file3.jpg']
    """
    
    matched_files = []
    
    # Determine the search pattern based on whether an extension is provided
    if extension:
        search_pattern = os.path.join(folder_path, f"**/*.{extension}")
    else:
        search_pattern = os.path.join(folder_path, "**/*" if recursive else "*")
    
    # Use glob to find matching files in the specified directory and subdirectories if recursive
    matched_files.extend(glob.glob(search_pattern, recursive=recursive))
    
    # If no files are found, return a list with an empty string
    if not matched_files:
        matched_files = [""]

    return matched_files


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
