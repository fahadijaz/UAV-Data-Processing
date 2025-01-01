from file_system_functions import find_files_in_folder

import os
import csv
import glob
import shutil
import pandas as pd
from datetime import datetime
from tqdm import tqdm # Progress Bar
import hashlib # Checksum of files before copying

def append_list_to_csv(data_list, comment, file_name='event.csv'):
    """
    Appends a list and a comment to a CSV file, with a timestamp added to each row.
    The list will be written as a single row, prefixed with the current timestamp.
    The comment will be written as a header row.

    Parameters:
    - data_list (list): The list of data to be written to the CSV file.
    - comment (str): A comment or description to be added as a header to the CSV.
    - file_name (str): The name of the CSV file to which the data will be appended. Defaults to 'event.csv'.
    """
    # Get the current timestamp in a readable format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Open the file in append mode
    with open(file_name, 'a', newline='') as f_object:
        writer_object = csv.writer(f_object)

        # Write the data list as a single row with the timestamp and comment
        writer_object.writerow([timestamp, comment] + data_list)
        # Close the file object
        f_object.close()



def append_dict_to_csv(data_dict, comment, file_name='event.csv'):
    """
    Appends a dictionary and a comment to a CSV file, with a timestamp added to each row.
    Each key-value pair from the dictionary will be written in a new row, with the timestamp included.

    Parameters:
    - data_dict (dict): The dictionary whose keys and values will be written to the CSV file.
    - comment (str): A comment or description to be added as a header to the CSV.
    - file_name (str): The name of the CSV file to which the data will be appended. Defaults to 'event.csv'.
    """
    # Get the current timestamp in a readable format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Open the file in append mode
    with open(file_name, 'a', newline='') as f_object:
        writer_object = csv.writer(f_object)

        # Write the comment as the first row (e.g., a header or description)
        writer_object.writerow([timestamp, comment])

        # Write each key-value pair from the dictionary in separate rows with the timestamp
        for key, value in data_dict.items():
            writer_object.writerow([timestamp, key, value])

        # Close the file object
        f_object.close()


# Funcion to check if two files are identicals or not
def calculate_md5(file_path, buffer_size=1024*1024):
    """
    Calculate the MD5 checksum of a file.
    
    :param file_path: Path to the file
    :param buffer_size: Number of bytes to read at a time (default is 1MB)
    :return: MD5 checksum as a hexadecimal string
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(buffer_size):
            md5.update(chunk)
    return md5.hexdigest()

# File copy function with progress bar
def copy_file_with_progress(src_file, dst, chk_size=True, buffer_size=1024*1024):
    """
    Copy a file from src_file to dst with a progress bar, content check, and metadata preservation.
    
    :param src_file: Source file path
    :param dst: Destination directory path
    :param chk_size: Flag to check file contents using checksum comparison (default is False)
    :param buffer_size: Number of bytes to read at a time (default is 1MB)
    """
    print(src_file)
    file_name = src_file.split('\\')[-1]
    
    # Check if the destination file already exists
    # Create dir if not exists
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=True)

    dst_file = os.path.join(dst, file_name)


    if os.path.exists(dst_file):
        print("File", '\033[1m', file_name, '\033[0m', "already exists in", '\033[1m', dst,'\033[0m',)
        
        # Only check contents if specified. Else skip copying if the file exists
        if chk_size:
            print(f"Checking contents...")
            # Calculate checksums for both files
            src_file_md5 = calculate_md5(src_file, buffer_size)
            dst_file_md5 = calculate_md5(dst_file, buffer_size)
    
            # If files are identical, skip the copy
            if src_file_md5 == dst_file_md5:
                print("Files are identical. Skipping copy.")
                return
            else:
                print("Files differ. Proceeding with copy.")
        else:
            print(f"Skipping copy.")
            return
    
    # If we reach here, it means the files are different or the destination doesn't exist
    print(f"Copying file from '{file_name}' to '{dst}'...")

    # Get the total size of the file for the progress bar
    total_size = os.path.getsize(src_file)
    
    # Open source and destination files
    with open(src_file, 'rb') as fsrc_file, open(dst_file, 'wb') as fdst:
        # Create a progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Copying", leave=False) as pbar:
            # Copy file in chunks and update the progress bar
            while True:
                # Read a chunk of data
                chunk = fsrc_file.read(buffer_size)
                if not chunk:
                    break
                # Write the chunk to the destination file
                fdst.write(chunk)
                # Update the progress bar
                pbar.update(len(chunk))
    
    # Copy file metadata (timestamps and permissions)
    shutil.copystat(src_file, dst_file)
    print("Metadata has been preserved.")

    # Now, verify that the source and destination files are identical using MD5 checksum
    print(f"Verifying if the source and destination files are identical...")
    src_file_md5 = calculate_md5(src_file, buffer_size)
    dst_file_md5 = calculate_md5(dst_file, buffer_size)
    
    if src_file_md5 == dst_file_md5:
        print(f"Verification successful: The files are identical.")
    else:
        print(f"Verification failed: The files are different.")

# Example usage:
# copy_file_with_progress("path/to/source/file", "path/to/destination")
# copy_file_with_progress(src, dst, True)


# Copy files, subfolders and files in sub folders
def copy_everything(src_dir, dest_dir, chk_size=True):
    """
    Recursively copies files and subdirectories from src_dir to dest_dir, preserving the directory structure.

    :param src_dir: Source directory to copy files from.
    :param dest_dir: Destination directory to copy files to.
    """
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)
    
    # Loop through each item in the source directory
    for item in os.listdir(src_dir):
        item_path_src = os.path.join(src_dir, item)
        item_path_dest = os.path.join(dest_dir, item)

        # If it's a file, copy with progress and content verification
        if os.path.isfile(item_path_src):
            copy_file_with_progress(item_path_src, dest_dir, chk_size=chk_size)

        # If it's a directory, recursively copy files within the subdirectory
        elif os.path.isdir(item_path_src):
            print(f"Copying subdir {item}.")
            # Recursively call the function for each subdirectory
            # Using copy tree function since this preserves the metadata for the sub folders as well
            # And copytree is faster than copy_file_with_progress since it does not perform filesize check
            shutil.copytree(item_path_src, item_path_dest, dirs_exist_ok=True)


def create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type):
    """
    Creates a dictionary of project paths for Pix4D projects, verifying whether each project folder exists.
    
    This function constructs a dictionary with project names as keys and their corresponding paths as values,
    based on the folder structure in the source directory. It also adds a path for the report folder if it exists.
    
    Parameters:
    - src_drive (str): The root drive path where the projects are stored.
    - path_pix4d_gnrl (str): The general folder path for the Pix4D projects.
    - field_id (str): The field ID used to identify the specific folder containing the projects.
    - flight_type (str): The type of flight (e.g., "drone", "aerial") used to further narrow down the project folder.
    
    Returns:
    - proj_dict (dict): A dictionary where keys are project names (starting with "2024") and values are the full
                         paths to the respective project folders. It also includes paths to report folders if available.
    - pix4d_path_src (str): The full path to the source Pix4D folder for reference.
    """
    # Print the status to indicate which field and flight type the function is processing.
    print(f"Preparing proj_dict for {field_id} flight type {flight_type}")
    
    # Generate the full source folder path for the Pix4D project files.
    pix4d_path_src = os.path.join(src_drive, path_pix4d_gnrl, field_id, flight_type)
    
    # List all folders in the main project directory
    folders = [name for name in os.listdir(pix4d_path_src) if os.path.isdir(os.path.join(pix4d_path_src, name))]

    # Filter the list of project folders to only include those starting with '2024'
    projects = [proj for proj in folders if proj[:4] == "2024"]
    
    # Initialize an empty dictionary to store project names and paths
    proj_dict = {}
    
    # Loop through each project folder, verifying that it exists before adding to the dictionary
    for proj in projects:
        path_proj = os.path.join(pix4d_path_src, proj)
        
        # Check if the project folder exists
        if os.path.exists(path_proj):
            proj_dict[proj] = [path_proj]  # Add the project path to the dictionary
        else:
            print(f"Path does not exist: {path_proj}")  # Print a message if the project folder is missing
    
    # For each project, if the path of report folder path does not exist in the dictionary, add it
    # Not using this path at the  moment. Just there in case.
    for proj_name in proj_dict:
        if len(proj_dict[proj_name]) == 1:  # If only the project folder is in the list
            report_path = os.path.join(proj_dict[proj_name][0], "1_initial", "report")
            if os.path.exists(report_path):
                proj_dict[proj_name].append(report_path)  # Add the report folder path to the dictionary
    
    # Return the project dictionary and the general source path for Pix4D projects
    return proj_dict, pix4d_path_src


def copy_p4d_log(dest_path, pix4d_path_src):
    """
    Copies Pix4D project files (.p4d) and log files from a source directory to a destination directory,
    using helper functions for better copy management and progress visibility.
    
    Parameters:
    - dest_path (str): The base destination drive or directory.
    - pix4d_path_src (str): The source path of the Pix4D project files.
    
    The function performs the following:
    1. Copies `.p4d` project files from the source to the destination, if they don't already exist.
    2. Searches for log directories containing "2024" in their name, creates the same directory structure
       in the destination, and copies `.log` files from the source if they don't already exist.
    
    Returns:
    - log_not_found (list): A list of directories where no `.log` file was found.
    """

    # Construct the destination project path based on the source path
    dest_proj_path = dest_path

    # List to store directories where no log files are found
    log_not_found = []

    # Iterate over each file/folder in the source Pix4D project path
    for file in os.listdir(pix4d_path_src):
        file_path_src = os.path.join(pix4d_path_src, file)

        # Check if the item is a file
        if os.path.isfile(file_path_src):
            # Copy only `.p4d` project files
            if file.endswith(".p4d"):
                dest_file_path = os.path.join(dest_proj_path, file)
                # Copy if the file does not exist in the destination
                if not os.path.exists(dest_file_path):
                    os.makedirs(dest_proj_path, exist_ok=True)
                    copy_file_with_progress(file_path_src, dest_proj_path)
                else:
                    print(f"Project file '{file}' already exists in '{dest_proj_path}'")

        # Check if the item is a directory
        if os.path.isdir(file_path_src):
            # Look for folders containing "2024" in their name
            if "2024" in file:
                # Create the corresponding destination directory if it doesn't exist
                dir_path_dest = os.path.join(dest_path, file_path_src.split("\\")[-1])
                os.makedirs(dir_path_dest, exist_ok=True)

                # Variable to track if a `.log` file is found within the folder
                log_found = False

                # Iterate over each file in the directory
                for subfile in os.listdir(file_path_src):
                    # Copy only `.log` files
                    if subfile.endswith(".log"):
                        log_found = True
                        dest_subfile_path = os.path.join(dir_path_dest, subfile)
                        # Copy if the log file does not exist in the destination
                        if not os.path.exists(dest_subfile_path):
                            subfile_path_src = os.path.join(file_path_src, subfile)
                            copy_file_with_progress(subfile_path_src, dir_path_dest)
                        else:
                            print(f"Log file '{subfile}' already exists in '{file}'")

                # If no `.log` files were found, add the directory name to log_not_found list
                if not log_found:
                    log_not_found.append(file)
                    print(f"No log files found for '{file}'")

    print("Copying Complete")
    if log_not_found:
        # Append the list of directories without logs to a CSV file for reference
        append_list_to_csv(log_not_found, "Logs not found")

    # Return the list of directories without logs
    return log_not_found

# Copying Reports for all projects
# This step overwrites all the files already in the destination dir with the same name
def copy_reports(dest_path, proj_dict):
    """
    Copies report directories and PDF reports from source projects to the destination directory.
    Overwrites any existing files with the same name in the destination.

    Parameters:
    - dest_path (str): Base destination path where the project reports should be copied.
    - proj_dict (dict): Dictionary of projects with their source paths.

    The function performs the following:
    1. Copies the entire report directory for each project from source to destination.
    2. Checks if the report directory exists in the source. If not, it notes the missing projects.
    3. Looks for any PDF file in the source report directory; if missing, it logs the absence.
    4. If a PDF file is found but does not match the expected naming convention, it logs it.

    Returns:
    - pdf_report_not_found (list): A list of projects where no PDF report was found.
    - report_does_not_exist (list): A list of projects where the report directory does not exist.
    - report_name_different (list): A list of projects where the PDF report does not match the naming convention.
    """

    # Initialize lists to track missing reports and PDF files
    pdf_report_not_found = []
    report_does_not_exists = []
    report_name_different = []

    # Iterate through each project in the project dictionary
    for proj_name, proj_info in proj_dict.items():
        src_path = proj_info[0]  # Get the source path for the current project
        dest_proj_path = os.path.join(dest_path, proj_name)  # Destination project path

        # Define source and destination report directories
        src_report_dir = os.path.join(src_path, r"1_initial\report")
        dest_report_dir = os.path.join(dest_proj_path, r"1_Report")

        # Check if the source report directory exists
        if not os.path.exists(src_report_dir):
            report_does_not_exists.append(proj_name)
            print(f"Report directory does not exist for project '{proj_name}'.")
        else:
            # Copy the entire report directory to the destination
            copy_everything(src_report_dir, dest_report_dir)

            # Check for the existence of the PDF report file in the source report directory
            pdf_report_found = False
            for file in os.listdir(src_report_dir):
                if file.lower().endswith('.pdf'):
                    pdf_report_found = True
                    
                    # Check if the PDF file matches the expected project naming convention
                    expected_pdf_name = f"{proj_name}_report.pdf"
                    if file != expected_pdf_name:
                        report_name_different.append(proj_name)
                        print(f"PDF report name does not match for project '{proj_name}'. Found: '{file}'")


            # Log if the PDF report was not found
            if not pdf_report_found:
                pdf_report_not_found.append(proj_name)
                print(f"PDF report for '{proj_name}' not found for project '{proj_name}'.")

    # Notify that copying is complete
    print("Copying Complete")


    # List of tuples containing the list and corresponding comments
    report_data = [
        (pdf_report_not_found, "PDF Report not found"),
        (report_does_not_exists, "Report folder does not exist"),
        (report_name_different, "Report with mismatching name")
    ]
    
    # Loop through each tuple and save to CSV if the list is not empty
    for report_list, comments in report_data:
        if report_list:
            append_list_to_csv(report_list, comments)

    # Return lists of projects with missing PDFs, report directories, and name mismatches
    return pdf_report_not_found, report_does_not_exists, report_name_different

def generate_project_paths(src_proj_path, dest_path, proj_name):
    """
    Generates source and destination directory paths for orthomosaic and point cloud data within a project,
    including only directories that exist in the source location.

    Parameters:
    - src_proj_path (str): Source path for the project data for project in question.
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_name (str): Project name used to determine the source directory structure.

    Returns:
    - dict: A dictionary containing the paths for orthomosaic (primary and extra) and point cloud data (both tif and all types),
            with the source paths as keys and corresponding destination paths as values.
    """
    # Construct the base destination path for the given project
    dest_proj_path = os.path.join(dest_path, proj_name)  # Destination path for the project
    
    # Initialize the dictionary to store paths for orthomosaics and point clouds
    project_paths = {
        "ortho_primary": {},
        "ortho_extra": {},
        "dsm_dtm": {},
        "mesh_extras": {}
    }
    
    # Define relative subdirectory paths for primary orthomosaic data (only tif)
    ortho_primary_subdirs = {
        "dsm_ortho": r"3_dsm_ortho\2_mosaic", 
        "blue": r"4_index\indices\Blue_blue", 
        "green": r"4_index\indices\Green_green", 
        "nir": r"4_index\indices\NIR_nir", 
        "red_edge": r"4_index\indices\Red_edge_red_edge", 
        "red": r"4_index\indices\Red_red", 
        "ndvi": r"4_index\indices\ndvi"
    }

    # Define relative subdirectory paths for extra orthomosaic data (only tif)
    ortho_extra_subdirs = {
        "grp_blue": r"4_index\indices\group1_blue", 
        "grp_grey": r"4_index\indices\group1_grayscale", 
        "grp_green": r"4_index\indices\group1_green", 
        "grp_red": r"4_index\indices\group1_red", 
        "reflectance_ortho": r"4_index\reflectance"
    }

    # Define relative subdirectory paths for point cloud data (tif)
    dsm_dtm_subdirs = {
        "dsm": r"3_dsm_ortho\1_dsm",  # Only tif
        "dtm": r"3_dsm_ortho\extras\dtm",  # Only tif
    }
    
    # Define relative subdirectory paths for point cloud data (copy all)
    point_cloud_all_subdirs = {
        "3d_mesh": r"2_densification\3d_mesh",  # Copy all
        "google_tiles": r"3_dsm_ortho\2_mosaic\google_tiles",  # Copy all
    }
    
    # Process the directories by calling helper function for each category
    project_paths["ortho_primary"] = process_directories(src_proj_path, dest_proj_path, ortho_primary_subdirs)
    project_paths["ortho_extra"] = process_directories(src_proj_path, dest_proj_path, ortho_extra_subdirs)
    project_paths["dsm_dtm"] = process_directories(src_proj_path, dest_proj_path, dsm_dtm_subdirs)
    project_paths["mesh_extras"] = process_directories(src_proj_path, dest_proj_path, point_cloud_all_subdirs)
    
    return project_paths

def process_directories(src_proj_path, dest_proj_path, subdirs):
    """
    Helper function to check if a directory exists and generate a dictionary of 
    source-destination paths for valid directories.

    Parameters:
    - src_proj_path (str): Source directory path for the specific project.
    - dest_proj_path (str): Destination directory path for the specific project.
    - subdirs (dict): Dictionary of subdirectory paths relative to the source base path.

    Returns:
    - dict: A dictionary mapping source paths to destination paths for directories that exist.
    """
    processed_paths = {}
    
    for key, subdir in subdirs.items():
        src_path = os.path.join(src_proj_path, subdir)
        dest_path = os.path.join(dest_proj_path, subdir)
        if os.path.exists(src_path):
            processed_paths[src_path] = dest_path
    
    return processed_paths

# # Example of usage with the updated function
# project_paths = generate_project_paths("/path/to/source", "/path/to/destination", "project_xyz")

# # Accessing the paths for different categories
# ortho_primary_paths = project_paths["ortho_primary"]
# ortho_extra_paths = project_paths["ortho_extra"]
# dsm_dtm_paths = project_paths["dsm_dtm"]
# mesh_all_paths = project_paths["mesh_extras"]


# Copying Orthomosaics
def copy_ortho(dest_path, proj_dict, combination, state_file, type_of_data_to_copy=["ortho_primary", "ortho_extra", "dsm_dtm", "mesh_extras"], chk_size=True):
    """
    Copies orthomosaic (tiff) files from the source project directories to destination directories, 
    including progress tracking. Creates missing destination directories and logs missing files.

    Parameters:
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_dict (dict): Dictionary containing project names as keys, and project details as values. Each project
                        entry has a source path at proj_dict[proj_name][0].
    - type_of_data_to_copy (list): List of data types to copy. Options include:
        - "ortho_primary": Primary orthomosaic files.
        - "ortho_extra": Extra orthomosaic files.
        - "dsm_dtm": DSM and DTM files.
        - "mesh_extras": Additional point cloud files.
        
    Returns:
    - tuple: A tuple containing three dictionaries:
      - `ortho_found_dict`: Project names mapped to lists of orthomosaics found and copied.
      - `mesh_found_dict`: Project names mapped to lists of point cloud files found and copied.
      - `mesh_extra_found_dict`: Project names mapped to lists of extra point cloud files found and copied.
    """
    
    ortho_found_dict = {}      # To store found and copied orthomosaic files per project
    mesh_found_dict = {}      # To store found and copied mesh files per project
    mesh_extra_found_dict = {}      # To store found and copied mesh extras per project
    
    # Print information about progress bar initialization
    print("Calculating number of files to be copied for the progress bar")

    # Calculate the total number of files to copy across all directories
    total_files_to_copy = 0
    for proj_name in proj_dict:
        src_proj_path = proj_dict[proj_name][0]  # Get the project base path
        dict_project_paths = generate_project_paths(src_proj_path, dest_path, proj_name)

        # Loop through each type of data to be copied and calculate the number of files
        for data_type in type_of_data_to_copy:
            dict_paths = dict_project_paths.get(data_type, {})

            for src_path in dict_paths.keys():
                if os.path.exists(src_path):
                    # If copying orthomosaics or DSM/DTM, count only .tif files
                    if data_type in ["ortho_primary", "ortho_extra", "dsm_dtm"]:
                        total_files_to_copy += len(find_files_in_folder(src_path, 'tif'))
                    # If copying mesh extras, count all files
                    elif data_type == "mesh_extras":
                        total_files_to_copy += len(find_files_in_folder(src_path, None, True))
        
    # Initialize the outer progress bar for the total number of files to copy
    with tqdm(total=total_files_to_copy, desc="Total Copy Progress", unit="file", leave=False) as total_pbar:
    
        # Iterate over each project to perform file copying
        projects_to_process = list(proj_dict.keys())  # Make a copy to avoid issues during modification

        # Iterate over each project to perform file copying
        for proj_name in projects_to_process:
        
            print(f"Processing data for project: {proj_name}")

            # Initialize flags and lists
            project_complete = True

            # Initialize empty lists for missing and found orthomosaics
            ortho_found = []
            mesh_found = []
            mesh_extra_found = []
            
            # Retrieve source and destination paths for orthomosaics and point clouds
            src_proj_path = proj_dict[proj_name][0]
            dest_proj_path = os.path.join(dest_path, proj_name)
            dict_project_paths = generate_project_paths(src_proj_path, dest_path, proj_name)
            
            # Customized folders for each data type
            dest_ortho_primary = os.path.join(dest_proj_path, "2_Orthomosaics")
            dest_ortho_extra = os.path.join(dest_proj_path, "2_Orthomosaics", "Extras")
            dest_dsm_dtm = os.path.join(dest_proj_path, "3_DSM_DTM_Elevation_Models")
            dest_mesh_extras = os.path.join(dest_proj_path, "3_DSM_DTM_Elevation_Models", "Point_Clouds_Extras")

               
            # Loop over the data types specified in type_of_data_to_copy
            for data_type in type_of_data_to_copy:
                dict_paths = dict_project_paths.get(data_type, {})

                # Choose the appropriate destination folder based on data type
                if data_type == "ortho_primary":
                    dest_folder = dest_ortho_primary
                elif data_type == "ortho_extra":
                    dest_folder = dest_ortho_extra
                elif data_type == "dsm_dtm":
                    dest_folder = dest_dsm_dtm
                elif data_type == "mesh_extras":
                    dest_folder = dest_mesh_extras
                else:
                    continue  # Skip any unknown data types

##
                # Choose the appropriate destination folder based on data type
                dest_folder = {
                    "ortho_primary": os.path.join(dest_proj_path, "2_Orthomosaics"),
                    "ortho_extra": os.path.join(dest_proj_path, "2_Orthomosaics", "Extras"),
                    "dsm_dtm": os.path.join(dest_proj_path, "3_DSM_DTM_Elevation_Models"),
                    "mesh_extras": os.path.join(dest_proj_path, "3_DSM_DTM_Elevation_Models", "Point_Clouds_Extras"),
                }.get(data_type, None)

                if not dest_folder:
                    continue  # Skip unknown data types
##

                for src_path in dict_paths.keys():
                    if not os.path.exists(src_path):
                        print(f"Source path '{src_path}' for data type '{data_type}' not found.")
                        project_complete = False
                        continue

                    # Check if project name in source path is the same as in destination path
                    if proj_name not in src_path:
                        print(f"""Warning-1: Project name mismatch! Source path {src_path}
                        does not contain the project name {proj_name}.""")
                        project_complete = False
                        break
                        
                    # Handle different types of data copying
                    if data_type in ["ortho_primary", "ortho_extra", "dsm_dtm"]:
                        # Copying required files (Orthomosaics or DSM/DTM) and relavant georeference files
                        tif_files = find_files_in_folder(src_path, 'tif')
                        prj_files = find_files_in_folder(src_path, 'prj')
                        tfw_files = find_files_in_folder(src_path, 'tfw')

                        files_to_copy = tif_files + prj_files + tfw_files
                        
                        for file_path in files_to_copy:
                            print(file_path)
                            file_name = os.path.basename(file_path)

                            # Updating log of files to be copied
                            if data_type in ["ortho_primary", "ortho_extra"]:
                                ortho_found.append(file_name)
                            else:
                                mesh_found.append(file_name)
                            print("Copying", file_path, dest_folder)
                            
                            # Checking if the proj_name is a part of source and destination paths
                            if proj_name in file_path and proj_name in dest_folder:

                                # Apply the condition for ortho_extra files so they are coped in the Extras folder
                                if "2_mosaic" in file_path and not '_mosaic_group1' in file_name:
                                    if "ortho_extra" in type_of_data_to_copy:
                                        copy_file_with_progress(file_path, dest_ortho_extra, chk_size=chk_size)
                                        total_pbar.update(1)  # Update progress bar
                                    else:
                                        continue
                                else:
                                    # Copy the file with progress tracking
                                    copy_file_with_progress(file_path, dest_folder, chk_size=chk_size)

                                    total_pbar.update(1)
                            else:
                                print(f"""Warning-2: Project name mismatch! 
                                Source path {file_path} or destination path {dest_folder} 
                                does not contain the project name {proj_name}.""")
                                project_complete = False

                    elif data_type == "mesh_extras":
                        # Checking if the proj_name is a part of source and destination paths
                        if proj_name in src_path and proj_name in dest_folder:
                            # Copying all files and directories for mesh extras
                            dest_subfolder = os.path.join(dest_folder, src_path.split("\\")[-1])
                            copy_everything(src_path, dest_subfolder, chk_size=chk_size)
    
                            # # Track all files found in mesh extras
                            # mesh_extra_files = find_files_in_folder(src_path, None, True)
                            # for mesh_file in mesh_extra_files:
                            #     file_name = os.path.basename(mesh_file)
                            #     mesh_extra_found.append(file_name)
                            #     total_pbar.update(1)
                        else:
                            print(f"""Warning-3: Project name mismatch! 
                            Source path {src_path} or destination path {dest_folder} 
                            does not contain the project name {proj_name}.""")
                            project_complete = False

            # Log missing and found orthomosaics and meshes to respective CSV files
            ortho_found_dict[proj_name] = ortho_found
            mesh_found_dict[proj_name] = mesh_found
            mesh_extra_found_dict[proj_name] = mesh_extra_found

            if project_complete:
                print(f"Project {proj_name} successfully copied. Removing from proj_dict.")
                del proj_dict[proj_name]
            else:
                print(f"Project {proj_name} not fully copied. Keeping it in proj_dict.")


            # Cleanup: Delete the state file after all projects are processed
            if len(proj_dict) == 0:
                if os.path.exists(state_file):
                    os.remove(state_file)
                print("All projects processed. State file removed.")
            else:
                # Save the updated state to disk
                save_proj_data(proj_dict, combination)
                
            # List of tuples containing the list, project name, and filename for CSV logging
            data_to_log = [
                (ortho_found, proj_name, 'ortho_list.csv'),
                (mesh_found, proj_name, 'mesh_list.csv'),
                (mesh_extra_found, proj_name, 'mesh_list.csv')
            ]

            # Loop through each tuple and log to CSV only if the list is not empty
            for data_list, project_name, filename in data_to_log:
                if data_list:  # Check if the list is not empty
                    append_list_to_csv(data_list, project_name, filename)

            
        # append_dict_to_csv(ortho_found_dict, f"LIST_ortho_found")
        # append_dict_to_csv(mesh_found_dict, f"LIST_mesh_found")
        # append_dict_to_csv(mesh_extra_found_dict, f"LIST_mesh_extra_found")

    # Print completion message and return dictionaries
    print("Copying complete")
    return ortho_found_dict, mesh_found_dict, mesh_extra_found_dict

import os
import json

def save_proj_data(proj_dict, proj_list, state_file="proj_dict_state_temp.json"):
    """
    Save a dictionary and a list to a specified file in JSON format.
    
    Parameters:
    - proj_dict (dict): The dictionary to save.
    - proj_list (list): The list to save.
    - state_file (str): The path to the file where data will be saved.
    """
    data = {
        "proj_dict": proj_dict,
        "proj_list": proj_list
    }
    with open(state_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {state_file}")
    
def load_proj_data(state_file="proj_dict_state_temp.json"):
    """
    Load a dictionary and a list from a specified file.
    
    Parameters:
    - state_file (str): The path to the file where data is stored.
    
    Returns:
    - tuple: A tuple containing the loaded dictionary and list.
    """
    if not os.path.exists(state_file):
        print("No existing state file found. Starting fresh.")
        return None, None
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        proj_dict = data.get("proj_dict", {})
        proj_list = data.get("proj_list", [])
        
        print(f"Data loaded from {state_file}")
        return proj_dict, proj_list