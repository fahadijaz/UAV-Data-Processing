from file_system_functions import find_files_in_folder

import os
import csv
import shutil
from tqdm import tqdm # Progress Bar
import hashlib # Checksum of files before copying
import glob
import pandas as pd




def append_list_to_csv(data_list, comment, file_name='event.csv'):
    """
    Appends a list and a comment to a CSV file.
    The list will be written as a single row, and the comment will be written as a header.

    Parameters:
    - data_list (list): The list of data to be written to the CSV file.
    - comment (str): A comment or description to be added as a header to the CSV.
    - file_name (str): The name of the CSV file to which the data will be appended. Defaults to 'event.csv'.
    """
    with open(file_name, 'a', newline='') as f_object:
        writer_object = csv.writer(f_object)

        # Write the comment as the first row (e.g., a header or description)
        writer_object.writerow([comment])

        # Write the list as a single row in the CSV
        writer_object.writerow(data_list)
        # Close the file object
        f_object.close()


def append_dict_to_csv(data_dict, comment, file_name='event.csv'):
    """
    Appends a dictionary and a comment to a CSV file.
    Each key-value pair from the dictionary will be written in a new row.

    Parameters:
    - data_dict (dict): The dictionary whose keys and values will be written to the CSV file.   
    - comment (str): A comment or description to be added as a header to the CSV.
    - file_name (str): The name of the CSV file to which the data will be appended. Defaults to 'event.csv'.
    """
    with open(file_name, 'a', newline='') as f_object:
        writer_object = csv.writer(f_object)

        # Write the comment as the first row (e.g., a header or description)
        writer_object.writerow([comment])

        # Write each key-value pair from the dictionary in separate rows
        for key, value in data_dict.items():
            writer_object.writerow([key, value])

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
def copy_file_with_progress(src_file, dst, chk_size=False, buffer_size=1024*1024):
    """
    Copy a file from src_file to dst with a progress bar, content check, and metadata preservation.
    
    :param src_file: Source file path
    :param dst: Destination directory path
    :param chk_size: Flag to check file contents using checksum comparison (default is False)
    :param buffer_size: Number of bytes to read at a time (default is 1MB)
    """

    file_name = src_file.split('\\')[-1]
    
    # Check if the destination file already exists
    # Create dir if not exists
    if not os.path.exists(dst):
        os.mkdir(dst)

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


# Copy files, subfolders and files in sub folders
def copy_everything(src_dir, dest_dir):
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
            copy_file_with_progress(item_path_src, dest_dir, chk_size=True)

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


# Copy all P4D Project Files and logs
def copy_p4d_log(dest_drive, pix4d_path_src):
    dest_proj_path = dest_drive+ pix4d_path_src[3:]
    for file in os.listdir(pix4d_path_src):
        log_not_found = []
        file_path_src = os.path.join(pix4d_path_src, file)
        # Checking if a certain item is a file or dir
        if os.path.isfile(file_path_src):
            if file[-4:] == ".p4d":
                # Copying only if the file does not already exists in the destination location
                if not os.path.exists(os.path.join(dest_proj_path, file)):
                    shutil.copy2(file_path_src, dest_proj_path)
                # If the files exists, then do not overwrite and display the following message
                else:
                    print("Project file", '\033[1m', file, '\033[0m', "already exists in", '\033[1m', dest_proj_path,'\033[0m',)    
    
        # Looking for log file
        log_found = False
        if os.path.isdir(file_path_src):
            # Filtering folders with 2024 in their name
            if "2024" in file:
                # Create the same dir in the destination
                dir_path_dest = dest_drive+file_path_src[3:]
                try:
                    os.mkdir(dir_path_dest)
                    # print(dir_path_dest, "created")
                # This will raise an error if the dir already exists. Adding exception to that error
                except FileExistsError:
                    # print(dir_path_dest, "already exists")
                    pass
                for subfile in os.listdir(file_path_src):
                    if subfile[-4:] == ".log":
                        log_found = True
                        # Copying only if the file does not already exists in the destination location
                        if not os.path.exists(os.path.join(dir_path_dest, subfile)):
                            subfile_path = os.path.join(file_path_src, subfile)
                            shutil.copy2(subfile_path, dir_path_dest)
                            # print("Log found", file)
                        # If the files exists, then do not overwrite and display the following message
                        else:
                            print("Log file", '\033[1m', subfile, '\033[0m', "already exists in", '\033[1m', file,'\033[0m',)        
                if not log_found:
                    log_not_found.append(file)
                    print("Log not found for ", file)
    print("Copying Complete")
    append_list_to_csv(log_not_found, "LIST of Logs not found")
    return(log_not_found)

# Copying Reports for all projects
# This step overwrites all the files already in the destination dir with the same name

def copy_reports(dest_path, proj_dict):
    pdf_report_not_found = []
    report_does_not_exists = []
    for proj_name in proj_dict:
        path = proj_dict[proj_name][0]
        dest_proj_path = os.path.join(dest_path, proj_name)
    
        # Copying all reports from all projects
        src_report_dir = path+r"\1_initial\report"
        dest_report_dir = dest_proj_path+r"\1_initial\report"
    
        # Checking if the report folder exists in the source project files
        if not os.path.exists(src_report_dir):
            report_does_not_exists.append(proj_name)
            print("Report does not does not exists for project ", proj_name)
        else:
            # Recursively copies files and subdirectories from src_dir to dest_dir, preserving the directory structure.
            copy_everything(src_report_dir, dest_report_dir)
            
            # Iterating through all files in the source dir
            # Check for pdf version of report present in there
            pdf_report_found = False
            for file in os.listdir(src_report_dir):
                if file == proj_name+"_report.pdf":
                    pdf_report_found = True

        
        if not pdf_report_found:
            pdf_report_not_found.append(proj_name)
            print("PDF report not found for ", proj_name)
    print("Copying Complete")

    append_list_to_csv(pdf_report_not_found, "LIST of PDF Reports not found")
    append_list_to_csv(report_does_not_exists, "LIST of Reports Folder does not exist")

    return(pdf_report_not_found, report_does_not_exists)

def ortho_paths(dest_path, proj_name, proj_dict):
    """
    Generates source and destination directory paths for orthomosaic data within a project,
    including only directories that exist in the source location.

    Parameters:
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_name (str): Project name, used as a key to retrieve the base source path.
    - proj_dict (dict): Dictionary containing project details, where proj_dict[proj_name][0]
                        provides the base path for the source data.

    Returns:
    - dict: A dictionary mapping each existing source orthomosaic directory to its corresponding
            destination directory.
    """
    # Base paths
    src_base_path = proj_dict[proj_name][0]
    dest_proj_path = os.path.join(dest_path, proj_name)
       
    # Define the relative paths for orthomosaic directories
    ortho_subdirs = {
        "dsm_ortho": r"3_dsm_ortho\2_mosaic",
        "reflectance_ortho": r"4_index\reflectance",
        "blue": r"4_index\indices\Blue_blue",
        "green": r"4_index\indices\Green_green",
        "grp_blue": r"4_index\indices\group1_blue",
        "grp_grey": r"4_index\indices\group1_grayscale",
        "grp_green": r"4_index\indices\group1_green",
        "grp_red": r"4_index\indices\group1_red",
        "ndvi": r"4_index\indices\ndvi",
        "nir": r"4_index\indices\NIR_nir",
        "red_edge": r"4_index\indices\Red_edge_red_edge",
        "red": r"4_index\indices\Red_red"
    }
    
    # Initialize dictionary to store mappings of existing source to destination paths
    dict_ortho = {}
    
    # Only add to dict_ortho if the source directory exists
    for subdir in ortho_subdirs.values():
        src_path = os.path.join(src_base_path, subdir)
        dest_path = os.path.join(dest_proj_path, subdir)
        
        if os.path.exists(src_path):  # Only add if source path exists
            dict_ortho[src_path] = dest_path

    return dict_ortho

def point_cloud_tif(dest_path, proj_name, proj_dict):
    """
    Generates source and destination directory paths for point cloud data within a project,
    including only directories that exist in the source location.

    Parameters:
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_name (str): Project name, used as a key to retrieve the base source path.
    - proj_dict (dict): Dictionary containing project details, where proj_dict[proj_name][0]
                        provides the base path for the source data.

    Returns:
    - dict: A dictionary mapping each existing source point cloud directory to its corresponding
            destination directory.
    """
    # Base paths
    src_base_path = proj_dict[proj_name][0]
    dest_proj_path = os.path.join(dest_path, proj_name)
    
    # List of relative subdirectory paths for point cloud data
    point_cloud_subdirs = [
        r"3_dsm_ortho\1_dsm", # Only tif
        r"3_dsm_ortho\extras\dtm", # Only tif
    ]
    # Initialize dictionary to store mappings of existing source to destination paths
    dict_mesh_tif = {}
    
    # Generate dict with existing source paths only
    dict_mesh_tif = {
        os.path.join(src_base_path, subdir): os.path.join(dest_proj_path, subdir)
        for subdir in point_cloud_subdirs
        if os.path.exists(os.path.join(src_base_path, subdir))
    }

    return dict_mesh_tif

def point_cloud_all(dest_path, proj_name, proj_dict):
    """
    Generates source and destination directory paths for point cloud data within a project,
    including only directories that exist in the source location.

    Parameters:
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_name (str): Project name, used as a key to retrieve the base source path.
    - proj_dict (dict): Dictionary containing project details, where proj_dict[proj_name][0]
                        provides the base path for the source data.

    Returns:
    - dict: A dictionary mapping each existing source point cloud directory to its corresponding
            destination directory.
    """
    # Base paths
    src_base_path = proj_dict[proj_name][0]
    dest_proj_path = os.path.join(dest_path, proj_name)
    
    # List of relative subdirectory paths for point cloud data
    point_cloud_subdirs = [
        r"2_densification\3d_mesh", # Copy all
        r"3_dsm_ortho\2_mosaic\google_tiles" # Copy all
    ]

    # Initialize dictionary to store mappings of existing source to destination paths
    dict_mesh_all = {}
    
    # Generate dict with existing source paths only
    dict_mesh_all = {
        os.path.join(src_base_path, subdir): os.path.join(dest_proj_path, subdir)
        for subdir in point_cloud_subdirs
        if os.path.exists(os.path.join(src_base_path, subdir))
    }

    return dict_mesh_all

# Copying Orthomosaics
def copy_ortho(dest_path, proj_dict):
    """
    Copies orthomosaic (tiff) files from the source project directories to destination directories, 
    including progress tracking. Creates missing destination directories and logs missing files.

    Parameters:
    - dest_path (str): Base path for the destination location where files should be copied.
    - proj_dict (dict): Dictionary containing project names as keys, and project details as values. Each project
                        entry has a source path at proj_dict[proj_name][0].

    Returns:
    - tuple: A tuple containing two dictionaries:
      - `ortho_found_dict`: Project names mapped to lists of orthomosaics found and copied.
      - `mesh_found_dict`: Project names mapped to lists of point cloud files found and copied.
    """
    
    ortho_found_dict = {}      # To store found and copied orthomosaic files per project
    mesh_found_dict = {}      # To store found and copied mesh files per project
    mesh_extra_found = {}      # To store found and copied mesh extras per project
    
    # Print information about progress bar initialization
    print("Calculating number of files to be copied for the progress bar")

    # Calculate the total number of files to copy across all directories
    total_files_to_copy = 0
    for proj_name in proj_dict:
        path = proj_dict[proj_name][0]  # Get the project base path
        dict_ortho = ortho_paths(dest_path, proj_name, proj_dict)  # Get source to destination orthomosaic paths
        dict_mesh_tif = point_cloud_tif(dest_path, proj_name, proj_dict)  # Get source to destination point cloud paths
        dict_mesh_all = point_cloud_all(dest_path, proj_name, proj_dict)  # Get source to destination point cloud paths

        list_src_ortho = list(dict_ortho.keys())  # List of source paths for orthomosaics
        list_src_mesh_tif = list(dict_mesh_tif.keys())   # List of source paths for point clouds ortho
        list_src_mesh_all = list(dict_mesh_all.keys())   # List of source paths for point clouds

        # Calculate the total number of .tif files in the source orthomosaic and point cloud directories
        if list_src_ortho+list_src_mesh_tif: # Porceeding if the list is not empty
            print(f"Calculating the number of orthomosaic files for {proj_name}")
            for src_path in list_src_ortho+list_src_mesh_tif:
                if os.path.exists(src_path):
                    total_files_to_copy += len(find_files_in_folder(src_path, 'tif'))

        if list_src_mesh_all: # Porceeding if the list is not empty
            print(f"Calculating the number of extras files for {proj_name}")
            for src_path in list_src_mesh_all:
                if os.path.exists(src_path):
                    total_files_to_copy += len(find_files_in_folder(src_path, None, True))

    # Initialize the outer progress bar for the total number of files to copy
    with tqdm(total=total_files_to_copy, desc="Total Copy Progress", unit="file", leave=False) as total_pbar:
    
        # Iterate over each project to perform file copying
        for proj_name in proj_dict:
            print(f"Copying Orthomosaics for {proj_name}")
            
            # Initialize empty lists for missing and found orthomosaics
            ortho_found = []
            mesh_found = []
            mesh_extra_found = []
            # Retrieve source and destination paths for orthomosaics and point clouds
            path = proj_dict[proj_name][0]
            dest_proj_path = os.path.join(dest_path, proj_name)
            dest_ortho_path = os.path.join(dest_proj_path, "2_orthomosaics")
            dest_mesh_path = os.path.join(dest_proj_path, "3_mesh")
            dest_mesh_path_extras = os.path.join(dest_proj_path, "4_extras")

            dict_ortho = ortho_paths(dest_path, proj_name, proj_dict)
            dict_mesh_tif = point_cloud_tif(dest_path, proj_name, proj_dict)
            dict_mesh_all = point_cloud_all(dest_path, proj_name, proj_dict)

            # Create destination directory for orthomosaics if it doesn't exist
            try:
                os.makedirs(dest_ortho_path, exist_ok=True)  # This handles both creation and skipping if exists
                os.makedirs(dest_mesh_path, exist_ok=True)  # This handles both creation and skipping if exists
                os.makedirs(dest_mesh_path_extras, exist_ok=True)  # This handles both creation and skipping if exists
                print(f"{dest_ortho_path}, {dest_mesh_path}, {dest_mesh_path_extras} created or already exists.")
            except Exception as e:
                print(f"Error creating one of the paths {dest_ortho_path}, {dest_mesh_path}, {dest_mesh_path_extras}: {e}")
                pass

            # Copy orthomosaic files from source to destination
            for src_path, dest_path_temp in dict_ortho.items():
                # Get a list of .tif files in the source directory
                ortho_tif_src = find_files_in_folder(src_path, 'tif')

                # Copy each orthomosaic file to the destination folder
                for ortho in ortho_tif_src:
                    ortho_file = os.path.basename(ortho)  # Extract the file name from the path
                    ortho_found.extend(ortho_file)

                    # Copy the file using a utility function that checks for differences before copying
                    copy_file_with_progress(ortho, dest_ortho_path, chk_size=True)
                    
                    # Update progress bar after each file is copied
                    total_pbar.update(1)
                    
            # Copy point cloud tif files from source to destination
            for src_path, dest_path_temp in dict_mesh_tif.items():
                # Get a list of all files in the source directory and sub directories
                mesh_files_src = find_files_in_folder(src_path, 'tif')

                # Copy each orthomosaic file to the destination folder
                for mesh in mesh_files_src:
                    mesh_file = os.path.basename(mesh)  # Extract the file name from the path
                    mesh_found.extend(mesh_file)
                    
                    # Copy the file using a utility function that checks for differences before copying
                    copy_file_with_progress(mesh, dest_mesh_path, chk_size=True)
                    
                    # Update progress bar after each file is copied
                    total_pbar.update(1)

          
            # Copy point cloud extras files and subfolders from source to destination
            for src_path, dest_path_temp in dict_mesh_all.items():
                # Copy the everything using a utility function that checks for differences before copying
                copy_everything(src_path, dest_path_temp):
                
                # Loop to update list and progress bar
                # Get a list of all files in the source directory and sub directories
                mesh_all_src = find_files_in_folder(src_path, None, True)
                for mesh in mesh_all_src:
                    mesh_file = os.path.basename(mesh)  # Extract the file name from the path
                    mesh_extra_found.extend(mesh_file)
                    # Update progress bar after each file is copied
                    total_pbar.update(1)
                    

            # Log missing and found orthomosaics to CSV files
            ortho_found_dict[proj_name] = ortho_found
            mesh_found_dict[proj_name] = mesh_found
            mesh_extra_found[proj_name] = mesh_extra_found

            append_list_to_csv(ortho_found, proj_name, 'ortho_list.csv')
            append_list_to_csv(mesh_found, proj_name, 'mesh_list.csv')
            append_list_to_csv(mesh_extra_found, proj_name, 'mesh_list.csv')

            
        append_dict_to_csv(ortho_found_dict, f"LIST_ortho_found")
        append_dict_to_csv(mesh_found_dict, f"LIST_mesh_found")
        append_dict_to_csv(mesh_extra_found, f"LIST_mesh_extra_found")

    # Print completion message and return dictionaries
    print("Copying complete")
    return ortho_not_found_dict, ortho_found_dict