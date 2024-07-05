import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_folders(base_path, band_names=["JPG", "TIF", "calibration"]):
    """
    Create folders for specified band names within the base path.
    """
    for band in band_names:
        band_folder = os.path.join(base_path, band)
        os.makedirs(band_folder, exist_ok=True)
    return band_names

def move_file(file, destination_folder):
    """
    Move a file to the destination folder with error handling.
    """
    try:
        shutil.move(file, destination_folder)
        logging.info(f"Moved {file} to {destination_folder}")
    except Exception as e:
        logging.error(f"Error moving file {file} to {destination_folder}: {e}")

def split_images_by_band(folder_path):
    """
    Split images into separate folders based on their file type (JPG, TIF)
    and move other files to a calibration folder.
    """
    # Create necessary folders
    create_folders(folder_path)
    
    for folder in os.listdir(folder_path):
        # Skip the target folders
        if folder in ["JPG", "TIF", "calibration"]:
            continue
        
        folder_full_path = os.path.join(folder_path, folder)
        
        # If the folder name does not follow the expected pattern, process files within it
        if folder.count('_') != 2:
            for file_name in os.listdir(folder_full_path):
                file_full_path = os.path.join(folder_full_path, file_name)

                if os.path.isfile(file_full_path):
                    # Move JPG files
                    if file_name.endswith("D.JPG"):
                        destination_folder = os.path.join(folder_path, "JPG")
                        move_file(file_full_path, destination_folder)
                    # Move TIF files
                    elif file_name.endswith(".TIF"):
                        destination_folder = os.path.join(folder_path, "TIF")
                        move_file(file_full_path, destination_folder)
                    # Move other files
                    else:
                        move_file(file_full_path, folder_path)

            # Remove the empty folder
            try:
                os.rmdir(folder_full_path)
                logging.info(f"Removed empty folder {folder_full_path}")
            except Exception as e:
                logging.error(f"Error removing folder {folder_full_path}: {e}")

        else:
            # Move files to the calibration folder
            for file_name in os.listdir(folder_full_path):
                file_full_path = os.path.join(folder_full_path, file_name)
                
                if os.path.isfile(file_full_path):
                    destination_folder = os.path.join(folder_path, "calibration")
                    move_file(file_full_path, destination_folder)
                    
            # Remove the empty folder
            try:
                os.rmdir(folder_full_path)
                logging.info(f"Removed empty folder {folder_full_path}")
            except Exception as e:
                logging.error(f"Error removing folder {folder_full_path}: {e}")

# Example usage
if __name__ == "__main__":
    # just an exsample folder, can be automated, take input from user. loop thru folder system.
    folder_path = "P:/PhenoCrop/Test_Folder/Test_ISAK/20240619 E166 M3M 30m MS"
    split_images_by_band(folder_path)
