from file_system_functions import find_files_in_folder

import os
import csv
import shutil
from tqdm import tqdm # Progress Bar
import hashlib # Checksum of files before copying
import glob
import pandas as pd
from itables import init_notebook_mode

init_notebook_mode(all_interactive=True)
from itables import show
# show(df, maxBytes=0)

# Showing index
import itables.options as opt
opt.showIndex = True

# Turning off downsampling of data while printing it
import itables.options as opt
opt.maxBytes = 0


def append_list_to_csv(list, comment):
    with open('event.csv', 'a') as f_object:
     
        # Pass this file object to csv.writer()
        # and get a writer object
        writer_object = csv.writer(f_object)
     
        # Pass the list as an argument into
        # the writerow()
        writer_object.writerow(comment)
        writer_object.writerow(list)     
        # Close the file object
        f_object.close()

def append_dict_to_csv(dict, comment):
    with open('event.csv', 'a') as f_object:
     
        # Pass this file object to csv.writer()
        # and get a writer object
        writer_object = csv.writer(f_object)
     
        # Pass the list as an argument into
        # the writerow()
        writer_object.writerow(comment)
        for key, value in dict.items():
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
    Copy  src_file to dst with a progress bar, content check, and metadata preservation.
    
    :param src_file: Source file path
    :param dst: Destination directory path
    :param buffer_size: Number of bytes to read at a time (default is 1MB)
    """

    file_name = src_file.split('\\')[-1]
    
    # Check if the destination file already exists
    if not os.path.exists(dst):
        os.mkdir(dst)

    dst_file = os.path.join(dst, file_name)


    if os.path.exists(dst_file):
        print(f"File '{dst_file}' already exists.")

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

# Example usage:
# copy_file_with_progress("path/to/source/file", "path/to/destination/file")


# Listing paths of all projects in the folder into a dict and checking if all dir exist 
# Returns a dict

def create_proj_dict(src_drive, path_pix4d_gnrl, field_id, flight_type):
    print("Preparing proj_dict for", field_id," flight type ", flight_type)
    # Genertating pix4d projects source folder path
    pix4d_path_src = src_drive+path_pix4d_gnrl+"\\"+field_id+"\\"+flight_type
    
    # Creating list of folder in the main dir
    folders = [name for name in os.listdir(pix4d_path_src) if os.path.isdir(os.path.join(pix4d_path_src, name))]
    # Filtering project folder names starting from 2024
    projects = [proj for proj in folders if proj[:4] == "2024"]

    proj_dict = {}
    for proj in projects:
        path_proj = pix4d_path_src+"\\"+proj
        if os.path.exists(path_proj):
            # print("Path Exists")
            proj_dict[proj] = [path_proj]
        else:
            print(path_proj)
            print("Path does not Exists")
        # print(path_proj)
    
    # Adding the path of the report for each project in the dict if it is not already there
    for proj_name in proj_dict:
        if len(proj_dict[proj_name]) == 1:
            proj_dict[proj_name].append(proj_dict[proj_name][0]+r"\1_initial\report")
    return(proj_dict, pix4d_path_src)



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

def copy_reports(dest_drive, proj_dict):
    pdf_report_not_found = []
    report_does_not_exists = []
    for proj_name in proj_dict:
        path = proj_dict[proj_name][0]
        dest_proj_path = dest_drive+ path[3:]
    
        # Copying all reports from all projects
        src_report_dir = path+r"\1_initial\report"
        # print(src_report_dir)
        dest_report_dir = dest_proj_path+r"\1_initial\report"
    
        # Checking if the report folder exists in the source project files
        if not os.path.exists(src_report_dir):
            report_does_not_exists.append(proj_name)
            print("Report does not does not exists for project ", proj_name)
    
        # Creating the whole path of parent and sub directories in the desired location
        try:
            os.makedirs(dest_report_dir)
            # print(dest_report_dir, "created")
        # This will raise an error if the dir already exists. Adding exception to that error
        except FileExistsError:
            # print(dest_report_dir, "already exists")
            pass
        
        # Copy all files from source to newly created destination directory 
        # Iterating through all files in the source dir
        # Check for pdf version of report present in there
        pdf_report_found = False
        for file in os.listdir(src_report_dir):
            file_path_src = os.path.join(src_report_dir, file)
            # Checking if a certain item is a file or dir
            if os.path.isfile(file_path_src):
                if file == proj_name+"_report.pdf":
                    pdf_report_found = True
                    # print("PDF report found for ", proj_name)
                # Copying only if the file does not already exists in the destination location
                if not os.path.exists(os.path.join(dest_report_dir, file)):
                    shutil.copy2(file_path_src, dest_report_dir)
                # If the files exists, then do not overwrite and display the following message
                else:
                    print("File", '\033[1m', file, '\033[0m', "already exists in", '\033[1m', dest_report_dir,'\033[0m',)
                
            # If dir then iterate through the files in subdir and copy them
            elif os.path.isdir(file_path_src):
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
                    subfile_path = os.path.join(file_path_src, subfile)
                    if os.path.isfile(subfile_path):
                        # Copying only if the file does not already exists in the destination location
                        if not os.path.exists(os.path.join(dest_drive, subfile_path[3:])):
                            shutil.copy2(subfile_path, dir_path_dest)
                        # If the files exists, then do not overwrite and display the following message
                        else:
                            print("File", '\033[1m', subfile, '\033[0m', "already exists in", '\033[1m', dir_path_dest,'\033[0m',)
                            
        if not pdf_report_found:
            pdf_report_not_found.append(proj_name)
            print("PDF report not found for ", proj_name)
    print("Copying Complete")

    append_list_to_csv(pdf_report_not_found, "LIST of PDF Reports not found")
    append_list_to_csv(report_does_not_exists, "LIST of Reports Folder does not exist")

    return(pdf_report_not_found, report_does_not_exists)

# Copying Orthomosaics
def copy_ortho(dest_drive, proj_dict):
    
    ortho_not_found_dict = {}
    ortho_found_dict = {}
    # ortho_copied_dict = {}



    dsm_ortho = r"\3_dsm_ortho\2_mosaic"
    reflectance_ortho = r"\4_index\reflectance"
    blue = r"\4_index\indices\Blue_blue"
    green = r"\4_index\indices\Green_green"
    grp_blue = r"\4_index\indices\group1_blue"
    grp_grey = r"\4_index\indices\group1_grayscale"
    grp_green = r"\4_index\indices\group1_green"
    grp_red = r"\4_index\indices\group1_red"
    ndvi = r"\4_index\indices\ndvi"
    nir = r"\4_index\indices\NIR_nir"
    red_edge = r"\4_index\indices\Red_edge_red_edge"
    red = r"\4_index\indices\Red_red"

    print("Calculating number of files to be copies for the progress bar")
    # Calculate the total number of files to copy across all directories
    total_files_to_copy = 0
    for proj_name in proj_dict:
        path = proj_dict[proj_name][0]
        
        src_dsm_ortho_dir = os.path.join(path+dsm_ortho)
        src_reflectance_ortho_dir = os.path.join(path+reflectance_ortho)
        src_blue_dir = os.path.join(path+blue)
        src_green_dir = os.path.join(path+green)
        src_grp_blue_dir = os.path.join(path+grp_blue)
        src_grp_grey_dir = os.path.join(path+grp_grey)
        src_grp_green_dir = os.path.join(path+grp_green)
        src_grp_red_dir = os.path.join(path+grp_red)
        src_ndvi_dir = os.path.join(path+ndvi)
        src_nir_dir = os.path.join(path+nir)
        src_red_edge_dir = os.path.join(path+red_edge)
        src_red_dir = os.path.join(path+red)
        # Add other directories as needed
        list_src_ortho = [src_dsm_ortho_dir, src_reflectance_ortho_dir,
                          src_blue_dir, src_green_dir,
                          src_grp_blue_dir, src_grp_grey_dir, src_grp_green_dir, src_grp_red_dir,
                          src_ndvi_dir, src_nir_dir, src_red_edge_dir, src_red_dir]
        
        print("Calculating for", proj_name)
        for src_path in list_src_ortho:
            if os.path.exists(src_path):
                total_files_to_copy += len(find_files_in_folder(src_path, 'tif'))


    # Outer progress bar for the total number of files across projects
    with tqdm(total=total_files_to_copy, desc="Total Copy Progress", unit="file", leave=False) as total_pbar:
    
        for proj_name in proj_dict:
            print("Copying Ortho for", proj_name)
                    
            ortho_not_found = []
            ortho_found = []
            # ortho_copied = []
            
            
            path = proj_dict[proj_name][0]
            dest_proj_path = dest_drive+ path[3:]
            dest_ortho_path = dest_drive+ path[3:] + r"\2_orthomosaics"
            
            # Copying ortho from 3_dsm_ortho
            src_dsm_ortho_dir = os.path.join(path+dsm_ortho)
            src_reflectance_ortho_dir = os.path.join(path+reflectance_ortho)
            src_blue_dir = os.path.join(path+blue)
            src_green_dir = os.path.join(path+green)
            src_grp_blue_dir = os.path.join(path+grp_blue)
            src_grp_grey_dir = os.path.join(path+grp_grey)
            src_grp_green_dir = os.path.join(path+grp_green)
            src_grp_red_dir = os.path.join(path+grp_red)
            src_ndvi_dir = os.path.join(path+ndvi)
            src_nir_dir = os.path.join(path+nir)
            src_red_edge_dir = os.path.join(path+red_edge)
            src_red_dir = os.path.join(path+red)
            
            list_src_ortho = [src_dsm_ortho_dir, src_reflectance_ortho_dir,
                              src_blue_dir, src_green_dir,
                              src_grp_blue_dir, src_grp_grey_dir, src_grp_green_dir, src_grp_red_dir,
                              src_ndvi_dir, src_nir_dir, src_red_edge_dir, src_red_dir]
            
            
            dest_dsm_ortho_dir = os.path.join(dest_proj_path+dsm_ortho)
            dest_reflectance_ortho_dir = os.path.join(dest_proj_path+reflectance_ortho)
            dest_blue_dir = os.path.join(dest_proj_path+blue)
            dest_green_dir = os.path.join(dest_proj_path+green)
            dest_grp_blue_dir = os.path.join(dest_proj_path+grp_blue)
            dest_grp_grey_dir = os.path.join(dest_proj_path+grp_grey)
            dest_grp_green_dir = os.path.join(dest_proj_path+grp_green)
            dest_grp_red_dir = os.path.join(dest_proj_path+grp_red)
            dest_ndvi_dir = os.path.join(dest_proj_path+ndvi)
            dest_nir_dir = os.path.join(dest_proj_path+nir)
            dest_red_edge_dir = os.path.join(dest_proj_path+red_edge)
            dest_red_dir = os.path.join(dest_proj_path+red)
            
            # Creating a list of destanation ortho folders if case we need to copy them to the respective folder in the destination
            list_dest_ortho = [dest_dsm_ortho_dir, dest_reflectance_ortho_dir,
                              dest_blue_dir, dest_green_dir,
                              dest_grp_blue_dir, dest_grp_grey_dir, dest_grp_green_dir, dest_grp_red_dir,
                              dest_ndvi_dir, dest_nir_dir, dest_red_edge_dir, dest_red_dir]
            
            # Create a dictionary mapping source to destination directories
            dict_ortho = dict(zip(list_src_ortho, list_dest_ortho))
            
            
            #Create Destination Folder for Orthomosaics
            try:
                os.mkdir(dest_ortho_path)
                print(dest_ortho_path, "created")
            # This will raise an error if the dir already exists. Adding exception to that error
            except FileExistsError:
                print(dest_ortho_path, "already exists")
                pass
                                
            for src_path, dest_path in dict_ortho.items():
                # Checking if the orthomosaic folder exists in the source project files
                if os.path.exists(src_path):
                    print(src_path)
                    # Returns a list of al tifs in the dir
                    ortho_tif_src = find_files_in_folder(src_path, 'tif')
                    ortho_found.extend(ortho_tif_src)

                    # Copying all orthomosaics one by one
                    for ortho in ortho_tif_src:
                        ortho_file = ortho.split('\\')[-1]
            
                        # This check if the same file already exists at teh destination. If it does, it checks if the contents are similar. Copies only
                        # if contents differ. Also shows a progress bar of the copying operation
                        copy_file_with_progress(ortho, dest_ortho_path, chk_size=True)
                        # ortho_copied.append(ortho_file)

                        # Update outer progress bar after each file
                        total_pbar.update(1)
                            
                else:
                    ortho_not_found.append(src_path)
        
        ortho_not_found_dict[proj_name] = ortho_not_found
        ortho_found_dict[proj_name] = ortho_found
        # ortho_copied_dict[proj_name] = ortho_copied
        append_list_to_csv(ortho_not_found_dict, "LIST ortho not found"+proj_name)
        append_list_to_csv(ortho_found_dict, "LIST ortho found"+proj_name)

    print("Complete")


    return(ortho_not_found_dict, ortho_found_dict)
