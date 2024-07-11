import os
import shutil
import logging
import pandas as pd
from tqdm import tqdm
import subprocess
from threading import Thread
from queue import Queue
import pytz
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set the logging format
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

class FileTransfer:
    def __init__(self, input_path=None, output_path=None, data_overview_file=None, flight_log=None):
        """
        Initializes the FileTransfer class with paths and overview file.

        Args:
            input_path (str): Path to the input directory.
            output_path (str): Path to the output directory.
            data_overview_file (str): Path to the CSV file containing data overview.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.number_of_elements = None
        self.nr_MS = 0
        self.nr_3D = 0
        self.nr_reflectance = 0
        self.flights_folders = []

        # List all directories in the input path
        self.direct = os.listdir(self.input_path)
        self.type_counts = {'MS': 0, '3D': 0, 'Reflectance': 0, 'phantom-MS':0}
        self.number_of_elements = len(self.direct)
        self.data_overview_file = data_overview_file
        self.flight_log_file = flight_log
        self.flight_log = pd.read_csv(self.flight_log_file)

        # Load the data overview file if provided, otherwise initialize an empty DataFrame
        if data_overview_file and os.path.exists(data_overview_file):
            self.data_overview = pd.read_csv(data_overview_file)
        else:
            logging.warning("Data overview file not found. Please create a new CSV file with the correct formatting.")
            create_csv = input("Do you want to create a new CSV file? (yes/no): ").strip().lower()
            if create_csv in ['yes', 'y']:
                self.data_overview = pd.DataFrame(columns=['FlightRoute', 'BasePath', 'BaseName'])
                self.data_overview[1]
                self.data_overview.to_csv(data_overview_file, index=False)
                logging.info(f"Created new CSV file: {data_overview_file}")
            else:
                raise FileNotFoundError("Data overview file is required to proceed.")
        
        # Log the input and output paths
        logging.info(f'Input Path: {self.input_path}\nOutput Path: {self.output_path}')


    def Phantomdata_system(self, directory):

        #print(f'flight with old phantomdrone detected,known phantom fileds:\n0. PhenoCrop')
        #user_input = input('type number of known route to map the flight')
        name_from_input = 'phantom-phenocrop-2024'
        dir_path = os.path.join(self.input_path, directory)
        start_file = os.listdir(dir_path)[4]
        end_file = os.listdir(dir_path)[-1]
        nr_files = len(os.listdir(dir_path))
        stat_start = datetime.fromtimestamp(os.stat(os.path.join(dir_path, start_file)).st_mtime)
        stat_end = datetime.fromtimestamp(os.stat(os.path.join(dir_path, end_file)).st_mtime)
        pass
        flight_info = {
            'dir_name': directory, 
            'flight_name': [name_from_input],
            'date': stat_start.strftime('%Y%m%d'),
            'ID': directory[:3],
            'start_time': stat_start.strftime('%H%M%S'),
            'end_time': stat_end.strftime('%H%M%S'),
            'type': ['phantom-MS'],
            'num_files':nr_files,
            'num_dir':1
        }

        self.flights_folders.append(flight_info)

    def get_information(self):
        """
        Gathers information from the directories in the input path and populates
        the flights_folders list with metadata for each directory.
        """
        try:
            dirs = sorted(os.listdir(self.input_path))

            for directory in dirs:
                if 'FPLAN' in directory or 'MEDIA' in directory:
                    #test for phantom data, if phantomdata implement system for it. 
                    self.Phantomdata_system(directory)
                else:

                    start_time, end_time = self.collect_timestamp(directory)
                    nr_files = len(os.listdir(directory))
                    flight_info = {
                        'dir_name': directory,
                        'flight_name': directory.split("_")[3:],
                        'date': directory.split("_")[1][:8],
                        'ID': directory.split("_")[2],
                        'start_time': start_time,
                        'end_time': end_time,
                        'type': [('MS' if 'MS' in directory else 'Reflectance' if directory.count('_') == 2 else '3D')],
                        'num_files':nr_files,
                        'num_dir': 1
                    }
                    self.flights_folders.append(flight_info)

                # Count each type of flight
                for flight in self.flights_folders:
                    flight_type = flight['type'][0]
                    if flight_type in self.type_counts:
                        self.type_counts[flight_type] += 1

            logging.info("Successfully gathered flight information.")
        except Exception as e:
            logging.error(f"Error gathering flight information: {e}")


    def collect_timestamp(self, directory):
        """
        Collects the start and end timestamps from the files in the given directory.

        Args:
            directory (str): The directory to collect timestamps from.

        Returns:
            tuple: A tuple containing the start and end timestamps.
        """
        try:
            dir_path = os.path.join(self.input_path, directory)
            files_sorted = sorted(os.listdir(dir_path))

            # Find the start time
            start_time = None
            for file in files_sorted:
                if 'JPG' in file:
                    start_time = file.split("_")[1][8:]
                    break

            # Find the end time
            end_time = files_sorted[-2].split("_")[1][8:] #input a if test to see if it is a JPG

            return start_time, end_time
        except Exception as e:
            logging.error(f"Error collecting timestamps for directory {directory}: {e}")
            return None, None

    def reflectance_types(self):
        """
        Determines the relationship between the number of reflectance panels and MS flights
        and calls the appropriate logic for handling them.
        """
        try:
            if self.type_counts['Reflectance'] == self.type_counts['MS'] and self.type_counts['MS']>0:
                logging.info('Found equal number of MS flights and reflectance panels.')
                self.reflectance_logic()
            elif self.type_counts['Reflectance'] > self.type_counts['MS']:
                self.reflectance_logic()
            else:
                if self.type_counts['Reflectance'] > 0:
                    # make system to duplicate reflectansepanel, and implement a check for MS flight found but no reflectance panel. 
                    logging.warning('More MS flights than reflectance panel images. You may need to ignore or duplicate some.')
                    self.reflectance_logic()
                else:
                    logging.warning('No folder found for reflectance panel for the MS flight. Still continue?')
        except Exception as e:
            logging.error(f"Error in reflectance_types: {e}")


    def reflectance_logic(self):
        """
        Handles the assignment of flight names to reflectance panels and vice versa
        to ensure proper pairing between MS flights and reflectance panels.
        """
        # Improve system by implementing timestamp checks for the reflectance panel
        try:
            n = 0
            while self.type_counts['Reflectance'] > 0 or self.type_counts['MS'] > 0:
                if n == 0:
                    n += 1
                    self.type_counts[self.flights_folders[0]['type'][0]] -= 1

                current_type = self.flights_folders[n]['type'][0]
                previous_type = self.flights_folders[n-1]['type'][0]

                if previous_type == 'Reflectance' and not self.flights_folders[n-1]['flight_name'] and current_type == 'MS':
                    self.flights_folders[n-1]['flight_name'] = self.flights_folders[n]['flight_name']
                elif previous_type == 'MS' and current_type == 'Reflectance' and self.type_counts['MS'] < self.type_counts['Reflectance']:
                    self.flights_folders[n]['flight_name'] = self.flights_folders[n-1]['flight_name']

                self.type_counts[current_type] -= 1
                n += 1

            logging.info("Reflectance logic applied successfully.")
        except Exception as e:
            logging.error(f"Error in reflectance_logic: {e}")

    def check_and_update_csv(self, flight_route):
        """
        Checks if a flight route exists in the data overview CSV file.
        If not, prompts the user to add the new flight route.

        Args:
            flight_route (str): The flight route to check.
        """
        # Improvments: Give suggestion base name and base path? 
        try:
            if not self.data_overview['FlightRoute'].str.contains(flight_route).any():
                logging.info(f"New flight route detected: {flight_route}")
                add_route = input(f"Do you want to add the flight route '{flight_route}' to the CSV file? (yes/no): ").strip().lower()
                if add_route in ['yes', 'y']:
                    base_name = input("Enter the corresponding base name for this flight route: ").strip()
                    base_path = input("Enter the corresponding base path for this flight route: ").strip()
                    self.add_flight_route_to_csv(flight_route, base_path, base_name)
                else:
                    raise ValueError(f"Flight route '{flight_route}' not added. Please update the CSV file to continue.")
            else:
                logging.info(f"Flight route '{flight_route}' already exists in the CSV file.")
        except Exception as e:
            logging.error(f"Error checking and updating CSV for flight route '{flight_route}': {e}")
            
    def add_flight_route_to_csv(self, flight_route, base_path, base_name):
        """
        Adds a new flight route to the data overview CSV file.

        Args:
            flight_route (str): The flight route to add.
            base_path (str): The base path for the flight route.
            base_name (str): The base name for the flight route.
        """
        try:
            new_entry = pd.DataFrame([{'FlightRoute': flight_route, 'BasePath': base_path, 'BaseName': base_name}])
            self.data_overview = pd.concat([self.data_overview, new_entry], ignore_index=True)
            self.data_overview.to_csv(self.data_overview_file, index=False)
            logging.info(f"Added new flight route '{flight_route}' with base path '{base_path}' and base name '{base_name}' to the CSV file.")
        except Exception as e:
            logging.error(f"Error adding flight route '{flight_route}' to CSV: {e}")

    def detect_and_handle_new_routes(self):
        """
        Detects new flight routes from the flights_folders list and checks
        and updates the CSV file accordingly.
        """
        try:
            for folder in self.flights_folders:
                flight_route = folder['flight_name']
                if flight_route:  # Ensure flight_route is not empty
                    self.check_and_update_csv(flight_route[0])
            logging.info("Flight routes detected and handled successfully.")
        except Exception as e:
            logging.error(f"Error detecting and handling new routes: {e}")

    def match(self):
        """
        Matches flight folders with their corresponding output paths
        based on the data overview.
        """
        try:
            for i, folder in enumerate(self.flights_folders):
                
                info = self.data_overview.loc[self.data_overview['FlightRoute'] == folder['flight_name'][0]]
                logging.info(f'type:')
                if not info.empty:
                    output_path = os.path.join(self.output_path, str(info['BasePath'].values[0]), str(folder['date'] +' '+str(info['BaseName'].values[0])))
                    self.flights_folders[i]['output_path'] = output_path
                else:
                    logging.warning(f"No matching route found for flight folder: {folder['dir_name']}")
            logging.info("Matching of flight folders with output paths completed successfully.")
        except Exception as e:
            logging.error(f"Error in matching flight folders: {e}")

    def print(self):
        """
        Prints a summary for 
        """
        for i, flight in enumerate(self.flights_folders):
                logging.info(f"{i}.Move: {flight['dir_name']:55} to location: {flight['output_path']}")
            

    def summary(self):
        """
        Provides a summary of the entire process by calling other methods
        and logging the results.
        """
        try:
            #self.merge_folders() #remove merge system
            self.get_information()  #new logic in finding ms flights, detect phantom flight
            self.reflectance_types()    #new logic in assigning the refleectanse panel
            self.detect_and_handle_new_routes()     #include a trashcan initialisation
            self.match()

            #for i, flight in enumerate(self.flights_folders):
            #    logging.info(f"{i}.Move: {flight['dir_name']:55} to location: {flight['output_path']}")
            
            while True:
                self.print()
                edit = input("Do you want to edit any output paths? (yes/no): ").strip().lower() # add option to duplicate, trash, move
                if edit in ['yes', 'y']:
                    type_edit = input("do you want to move, duplicate, or trash? (move/duplicate/trash)")
                    if type_edit in ['move', 'm']:
                        try:
                            flight_index = int(input("Enter the number corresponding to the flight you want to edit: "))
                            new_path_index = int(input("Enter the number corresponding to the flight whose path you want to use: "))

                            # Validate the indices
                            if 0 <= flight_index < len(self.flights_folders) and 0 <= new_path_index < len(self.flights_folders):
                                self.flights_folders[flight_index]['output_path'] = self.flights_folders[new_path_index]['output_path']
                                logging.info(f"Updated: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[flight_index]['output_path']}")
                            else:
                                logging.warning("Invalid indices entered. Please try again.")
                        except ValueError:
                            logging.error("Invalid input. Please enter numbers corresponding to the flight indices.")
                    elif type_edit in ['duplicate', 'd']:
                        flight_index = int(input("Enter the number corresponding to the flight you want to duplicate: "))
                        new_path_index = int(input("Enter the number corresponding to the flight whose path you want to use: "))
                        # Validate the indices
                        if 0 <= flight_index < len(self.flights_folders) and 0 <= new_path_index < len(self.flights_folders):
                            temp = self.flights_folders[flight_index]
                            temp['output_path'] = self.flights_folders[new_path_index]['output_path']
                            self.flights_folders.append(temp)
                            logging.info(f"duplicated: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[flight_index]['output_path']}")
                        else:
                            logging.warning("Invalid indices entered. Please try again.")

                    elif type_edit in ['trash', 't']:
                        flight_index = int(input("Enter the number corresponding to the flight you want to trash: "))
                        if 0 <= flight_index < len(self.flights_folders):
                                info = self.data_overview.loc[self.data_overview['FlightRoute'] == self.flights_folders[flight_index]['flight_name'][0]]
                                output_path = os.path.join(self.output_path, '_TRASHCAN\\'+ str(info['BasePath'].values[0]), str(self.flights_folders[flight_index]['date'] +' '+str(info['BaseName'].values[0])))
                                self.flights_folders[flight_index]['output_path'] = output_path
                                self.flights_folders[flight_index]['flight_name'] = self.flights_folders[flight_index]['flight_name']+'_trashed_flight'

                                logging.info(f"Updated: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[flight_index]['output_path']}")
                        else:
                            logging.warning("Invalid indices entered. Please try again.")

                else:
                    break
                
        except Exception as e:
            logging.error(f"Error in summary: {e}")


    @staticmethod
    def move_directory(source_path, destination_path):
        try:
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Execute the xcopy command
            source_path = f'"{source_path}\\*"'  # Ensure the source path is quoted and includes all files
            destination_path = f'"{destination_path}\\"'  # Ensure the destination path is quoted and has a trailing backslash
            command = f'xcopy {source_path} {destination_path} /E /I /Y'
            #print("Command to run:", command)  # Debugging output

            # Execute the command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)


            #result = subprocess.run(['xcopy', f'"{source_path}\\*"', f'"{destination_path}\\"'], capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error copying {source_path} to {destination_path}: {result.stderr}")
            else:
                logging.info(f"Completed moving directory {source_path} to {destination_path}")
                try:
                    #shutil.rmtree(source_path)  # Use shutil.rmtree to delete directories
                    #print(f"Successfully deleted source directory: {source_path}")
                    pass
                except Exception as e:
                    print(f"Failed to delete source directory: {source_path}. Error: {e}")


        except Exception as e:
            logging.error(f"Exception moving {source_path} to {destination_path}: {e}")

    def move_files_to_output(self):
        total_folders = len(self.flights_folders)
        q = Queue()
        threads = []

        # Create a progress bar
        pbar = tqdm(total=total_folders, desc="Moving directories", unit="dir")

        # Thread target function to perform the moves
        def worker():
            while not q.empty():
                source_path, destination_path = q.get()
                self.move_directory(source_path, destination_path)
                pbar.update(1)
                q.task_done()

        # Queueing tasks
        for flight in self.flights_folders:
            source_path = os.path.join(self.input_path, flight['dir_name'])
            destination_path = os.path.join(flight['output_path'], flight['dir_name'])
            q.put((source_path, destination_path))

        # Starting threads
        for _ in range(min(10, total_folders)):  # Limit number of threads to prevent overloading
            t = Thread(target=worker)
            t.start()
            threads.append(t)

        # Wait for all threads to finish
        for t in threads:
            t.join()

        pbar.close()
        self.save_flight_log()
        final_user_input = input("Do you want to remove the files form the sd card?(yes/no)")
        if final_user_input in ['yes', 'y']:
            self.close_and_whipe_sd_cards()
    
    def save_flight_log(self):
        
        
        df = pd.read_csv(self.flight_log_file)
        logging.info(f"initial csv {df} ")#to {self.flight_log}")
        for flight in self.flights_folders:
                dir_name = flight['dir_name']
                flight_name = str(flight['flight_name'][0]).strip()
                date = str(flight['date']).strip()
                ID = flight['ID']
                start_time = flight['start_time']
                end_time = flight['end_time']
                flight_type = flight['type'][0]
                num_files = str(flight['num_files'])
                num_dir = 1
                output_path = flight['output_path']

                # Find existing entry with the same date and flight name
                existing_entry = df[(df['date'] == date) & (df['flight_name'] == flight_name)]

                if not existing_entry.empty:
                    # Update existing entry
                    idx = existing_entry.index[0]
                    df.at[idx, 'dir_name'] += f", {dir_name}"
                    df.at[idx, 'ID'] += f", {ID}"
                    df.at[idx, 'type'] += f", {flight_type}"
                    df.at[idx, 'num_files'] += f", {num_files}"
                    df.at[idx, 'num_dir'] += num_dir

                    # Compare and update start_time and end_time
                    df.at[idx, 'start_time'] = min(df.at[idx, 'start_time'], start_time)
                    df.at[idx, 'end_time'] = max(df.at[idx, 'end_time'], end_time)
                else:
                    # Add new entry
                    new_entry = {
                        "dir_name": dir_name,
                        "flight_name": flight_name,
                        "date": date,
                        "ID": ID,
                        "start_time": start_time,
                        "end_time": end_time,
                        "type": flight_type,
                        "num_files": num_files,
                        "num_dir": num_dir,
                        "output_path": output_path
                    }
                    new_entry = pd.DataFrame([new_entry])
                    df = pd.concat([df,new_entry], ignore_index=True)
        logging.info(f"updated csv {df} ")
            # Write the updated DataFrame back to the CSV file
        df.to_csv(self.flight_log_file, index=False)


    def close_and_whipe_sd_cards(self):
        shutil.rmtree(self.input_path)  # Use shutil.rmtree to delete directories


if __name__ == "__main__":

    def detect_sd_cards2():
        """
        Detects available SD cards by checking known drive paths.
        Returns a list of valid SD card paths.
        """
        potential_paths = ["G:/DCIM", "I:/DCIM", "D:/DCIM"]
        available_paths = [path for path in potential_paths if os.path.exists(path)]
        return available_paths
    
    def detect_sd_cards():
        """
        Detects available SD cards by checking known drive paths.
        Returns a list of valid SD card paths.
        """
        potential_paths = ["G:/DCIM", "I:/DCIM", "D:/DCIM"]
        available_paths = []

        for path in potential_paths:
            try:
                with os.scandir(path) as entries:
                    if any(entries):
                        available_paths.append(path)
            except FileNotFoundError:
                continue

        return available_paths
    # Initialize variables
    output_path = "P:\\PhenoCrop\\1_flights"
    #output_path = "P:\\PhenoCrop\\Test_Folder\\Test_ISAK\\test_output"
    data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
    flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"

    # Detect available SD cards
    sd_card_paths = detect_sd_cards2()
    logging.info(f'SD cards detected:{[p for p in sd_card_paths]}')
    # List to store FileTransfer instances
    file_transfers = []

    # Process each detected SD card
    for sd_card_path in sd_card_paths:
        ft = FileTransfer(input_path=sd_card_path, output_path=output_path, data_overview_file=data_file, flight_log=flight_log)
        ft.summary()
        file_transfers.append(ft)
        
    # Move files for all processed SD cards
    move = input('Do you want to move the files? (yes/no): ').strip().lower()
    if move in ['yes', 'y']:
        for ft in file_transfers:
            ft.move_files_to_output()
        logging.info('Files moved successfully')

# added functonality: sort the phantomdata, new reflectansepanel logic. write information to csv, for automatic infill of flight information. add better progressbar, folder size in metadata, uptade frequantly. 