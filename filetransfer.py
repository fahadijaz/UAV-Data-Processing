import os
import shutil
import logging
import pandas as pd
import copy
import subprocess
from tqdm import tqdm
from threading import Thread
from queue import Queue
from datetime import datetime
from typing import List, Tuple


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class FileTransfer:
    def __init__(self, input_path: str, output_path: str, data_overview_file: str, flight_log: str):
        self.input_path = input_path
        self.output_path = output_path
        self.data_overview_file = data_overview_file
        self.flight_log_file = flight_log
        self.temp_log_file = "P:\\PhenoCrop\\0_csv\\temp_flight_log.csv"
        self.type_counts = {'MS': 0, '3D': 0, 'Reflectance': 0, 'phantom-MS': 0}
        self.flights_folders = []


        self._load_data_overview()
        self.temp_flight_log = self._load_flight_log(self.temp_log_file)
        self._list_directories()

    def _load_data_overview(self):
        if os.path.exists(self.data_overview_file):
            self.data_overview = pd.read_csv(self.data_overview_file)
            logging.info(f"Csv loaded successfully: {self.data_overview_file}")
        else:
            self.data_overview = pd.DataFrame(columns=['FlightRoute', 'BasePath', 'BaseName'])
            self.data_overview.to_csv(self.data_overview_file, index=False)
            logging.warning("Data overview file not found. Created a new CSV file.")

    @staticmethod
    def _load_flight_log(log_file):
        if os.path.exists(log_file):
            flight_log = pd.read_csv(log_file)
        else:
            flight_log = pd.DataFrame(columns=[
                "dir_name", "flight_name", "date", "folder_ID", "start_time",
                "end_time", "type", "num_files", "num_dir", "output_path", "height"
            ])
            flight_log.to_csv(log_file, index=False)
            logging.warning("Flight log file not found. Created a new CSV file.")
        return flight_log

    def _list_directories(self):
        self.direct = os.listdir(self.input_path)
        self.number_of_elements = len(self.direct)

    def get_information(self):
        dirs = sorted(os.listdir(self.input_path))
        for directory in dirs:
            if 'FPLAN' in directory or 'MEDIA' in directory:
                self.Phantomdata_system(directory)
            else:
                self._process_directory(directory)
        self._count_flight_types()
        logging.info("Successfully gathered flight information.")

    def _process_directory(self, directory: str):
        dir_path = os.path.join(self.input_path, directory)
        start_time, end_time = self._collect_timestamp(directory)
        nr_files = len(os.listdir(dir_path))
        flight_info = {
            'dir_name': directory,
            'flight_name': directory.split("_")[3:],
            'date': directory.split("_")[1][:8],
            'folder_ID': directory.split("_")[2],
            'start_time': start_time,
            'end_time': end_time,
            'type': 'MS' if 'MS' in directory else 'Reflectance' if directory.count('_') == 2 else '3D',
            'num_files': nr_files,
            'num_dir': 1
        }
        self.flights_folders.append(flight_info)

    def _collect_timestamp(self, directory: str) -> Tuple[str, str]:
        try:
            dir_path = os.path.join(self.input_path, directory)
            files_sorted = sorted(os.listdir(dir_path))
            start_time = files_sorted[4].split("_")[1][8:]
            end_time = files_sorted[-2].split("_")[1][8:]
            return start_time, end_time
        except Exception as e:
            logging.error(f"Error collecting timestamps for directory {directory}: {e}")
            return None, None

    def _count_flight_types(self):
        for flight in self.flights_folders:
            flight_type = flight['type']
            if flight_type in self.type_counts:
                self.type_counts[flight_type] += 1
        self._check_reflectance_panel_files()

    def Phantomdata_system(self, directory: str):
        name_from_input = 'phantom-phenocrop-2024'
        dir_path = os.path.join(self.input_path, directory)
        start_file = os.listdir(dir_path)[4]
        end_file = os.listdir(dir_path)[-1]
        nr_files = len(os.listdir(dir_path))
        stat_start = datetime.fromtimestamp(os.stat(os.path.join(dir_path, start_file)).st_mtime)
        stat_end = datetime.fromtimestamp(os.stat(os.path.join(dir_path, end_file)).st_mtime)
        flight_info = {
            'dir_name': directory,
            'flight_name': [name_from_input],
            'date': stat_start.strftime('%Y%m%d'),
            'folder_ID': directory[:3],
            'start_time': stat_start.strftime('%H%M%S'),
            'end_time': stat_end.strftime('%H%M%S'),
            'type': 'phantom-MS',
            'num_files': nr_files,
            'num_dir': 1
        }
        self.flights_folders.append(flight_info)


        try:
            n = 0
            while self.type_counts['Reflectance'] > 0 or self.type_counts['MS'] > 0:
                if n == 0:
                    n += 1
                    self.type_counts[self.flights_folders[0]['type']] -= 1

                current_type = self.flights_folders[n]['type']
                previous_type = self.flights_folders[n-1]['type']

                if previous_type == 'Reflectance' and not self.flights_folders[n-1]['flight_name'] and current_type == 'MS':
                    self.flights_folders[n-1]['flight_name'] = self.flights_folders[n]['flight_name']
                elif previous_type == 'MS' and current_type == 'Reflectance' and self.type_counts['MS'] < self.type_counts['Reflectance']:
                    self.flights_folders[n]['flight_name'] = self.flights_folders[n-1]['flight_name']

                self.type_counts[current_type] -= 1
                n += 1
            logging.info("Reflectance logic applied successfully.")
        except Exception as e:
            logging.error(f"Error in reflectance_logic: {e}")

    def reflectance_logic_with_timestamps(self):
        try:
            required_tif_files = ["G.TIF", "R.TIF", "NIR.TIF", "RE.TIF"]

            # Validate reflectance panels
            for folder in self.flights_folders:
                if folder['type'] == 'Reflectance':
                    if not self._has_required_tif_files(folder, required_tif_files):
                        logging.warning(f"Missing required .tif files in reflectance folder: {folder['dir_name']}")
                        folder['valid'] = False
                    else:
                        folder['valid'] = True

            # Initialize 'reflectance_assigned' attribute for MS flights
            for folder in self.flights_folders:
                if folder['type'] == 'MS':
                    folder['reflectance_assigned'] = False

            # Sort by start time
            self.flights_folders.sort(key=lambda x: datetime.strptime(x['start_time'], '%H%M%S'))

            n = 0
            while n < len(self.flights_folders):
                current_type = self.flights_folders[n]['type']

                if current_type == 'Reflectance' and self.flights_folders[n]['valid']:
                    closest_ms_flight = None
                    min_time_diff = float('inf')
                    reflectance_panel = self.flights_folders[n]

                    for ms_flight in self.flights_folders:
                        if ms_flight['type'] == 'MS' and not ms_flight['reflectance_assigned']:
                            panel_start_time = datetime.strptime(reflectance_panel['start_time'], '%H%M%S')
                            panel_end_time = datetime.strptime(reflectance_panel['end_time'], '%H%M%S')
                            ms_start_time = datetime.strptime(ms_flight['start_time'], '%H%M%S')
                            ms_end_time = datetime.strptime(ms_flight['end_time'], '%H%M%S')

                            if panel_end_time < ms_start_time:  # Panel ends before MS flight starts
                                time_diff = (ms_start_time - panel_end_time).total_seconds()
                            elif panel_start_time > ms_end_time:  # Panel starts after MS flight ends
                                time_diff = (panel_start_time - ms_end_time).total_seconds()
                            else:
                                time_diff = 0  # Overlapping or same time

                            if time_diff < min_time_diff:
                                min_time_diff = time_diff
                                closest_ms_flight = ms_flight

                    if closest_ms_flight:
                        reflectance_panel['flight_name'] = closest_ms_flight['flight_name']
                        closest_ms_flight['reflectance_assigned'] = True
                        logging.info(f"Assigned reflectance panel {reflectance_panel['dir_name']} to MS flight {closest_ms_flight['dir_name']}")
                    else:
                        logging.warning(f"No valid MS flight found for reflectance panel: {reflectance_panel['dir_name']}")

                n += 1

            logging.info("Reflectance logic with timestamps applied successfully.")
        except Exception as e:
            logging.error(f"Error in reflectance_logic_with_timestamps: {e}")

    def _has_required_tif_files(self, folder, required_files):
        folder_path = os.path.join(self.input_path, folder['dir_name'])
        existing_files = os.listdir(folder_path)
        return all(any(req_file in file for file in existing_files) for req_file in required_files)

    def _suggest_duplicate_panel(self, ms_flight, reflectance_panels):
        try:
            closest_panel = None
            min_time_diff = float('inf')
            for panel in reflectance_panels:
                time_diff = abs(datetime.strptime(ms_flight['start_time'], '%H%M%S') - datetime.strptime(panel['start_time'], '%H%M%S')).total_seconds()
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_panel = panel

            if closest_panel:
                suggest_duplicate = input(f"Do you want to duplicate the nearest reflectance panel '{closest_panel['dir_name']}' for the MS flight '{ms_flight['dir_name']}'? (yes/no): ").strip().lower()
                if suggest_duplicate in ['yes', 'y']:
                    self._duplicate_reflectance_panel(ms_flight, closest_panel)
        except Exception as e:
            logging.error(f"Error in suggest_duplicate_panel: {e}")

    def _duplicate_reflectance_panel(self, ms_flight, reflectance_panel):
        try:
            new_panel = reflectance_panel.copy()
            new_panel['dir_name'] = f"{reflectance_panel['dir_name']}_duplicate"
            self.flights_folders.append(new_panel)
            ms_flight['flight_name'].extend(new_panel['flight_name'])
            logging.info(f"Duplicated reflectance panel '{reflectance_panel['dir_name']}' for MS flight '{ms_flight['dir_name']}'.")
        except Exception as e:
            logging.error(f"Error in duplicate_reflectance_panel: {e}")

    def _check_reflectance_panel_files(self):
        required_files = ["G.TIF", "R.TIF", "NIR.TIF", "RE.TIF"]
        for folder in self.flights_folders:
            if folder['type'] == 'Reflectance':
                files = os.listdir(os.path.join(self.input_path, folder['dir_name']))
                missing_files = [f for f in required_files if not any(f in file for file in files)]
                if missing_files:
                    logging.warning(f'Missing {missing_files} in reflectance folder: {folder["dir_name"]}')

    def detect_and_handle_new_routes(self):
        try:
            for folder in self.flights_folders:
                flight_route = folder['flight_name']
                if flight_route:
                    self._check_and_update_csv(flight_route[0])
            logging.info("Flight routes detected and handled successfully.")
        except Exception as e:
            logging.error(f"Error detecting and handling new routes: {e}")

    def _check_and_update_csv(self, flight_route: str):
        if not self.data_overview['FlightRoute'].str.contains(flight_route).any():
            logging.info(f"New flight route detected: {flight_route}")
            add_route = input(f"Do you want to add the flight route '{flight_route}' to the CSV file? (yes/no): ").strip().lower()
            if add_route in ['yes', 'y']:
                base_name = input("Enter the corresponding base information for this flight route(foldername|drone|height|type|overlap): ").strip()
                self._add_flight_route_to_csv(flight_route, base_name)
            else:
                raise ValueError(f"Flight route '{flight_route}' not added. Please update the CSV file to continue.")
        else:
            logging.info(f"Flight route '{flight_route}' already exists in the CSV file.")

    def _add_flight_route_to_csv(self, flight_route: str, base_info: str):
        try:
            info = base_info.split(" ")
            base_name = info[0]
            base_drone = info[1]
            base_height = info[2]
            base_type = info[3]
            base_overlap = f'{info[4]} {info[5]}'
            base_path = f'{base_name}/{base_type}'
            new_entry = pd.DataFrame([{
                'FlightRoute': flight_route, 'BasePath': base_path, 'BaseName': base_name,
                'BaseDrone': base_drone, 'BaseHeight': base_height, 'BaseType': base_type, 'BaseOverlap': base_overlap
            }])
            self.data_overview = pd.concat([self.data_overview, new_entry], ignore_index=True)
            self.data_overview.to_csv(self.data_overview_file, index=False)
            logging.info(f"Added new flight route '{flight_route}' with base path '{base_path}' and base name '{base_name}' to the CSV file.")
        except Exception as e:
            logging.error(f"Error adding flight route '{flight_route}' to CSV: {e}")

    def match(self):
        try:
            for i, folder in enumerate(self.flights_folders):
                if folder['flight_name'] != []:
                    
                    info = self.data_overview.loc[self.data_overview['FlightRoute'] == folder['flight_name'][0]]
                    if not info.empty:
                        output_path = os.path.join(self.output_path, str(info['BasePath'].values[0]), f"{str(folder['date'])} {str(info['BaseName'].values[0])} {str(info['BaseDrone'].values[0])} {str(info['BaseHeight'].values[0])} {str(info['BaseType'].values[0])} {str(info['BaseOverlap'].values[0])}")
                        self.flights_folders[i]['output_path'] = output_path
                        self.flights_folders[i]['height'] = info['BaseHeight'].values[0]
                    else:
                        logging.warning(f"No matching route found for flight folder: {folder['dir_name']}")
                else:
                    output_path = os.path.join(self.output_path,'_NO_MATCH')
                    self.flights_folders[i]['output_path'] = output_path
                    self.flights_folders[i]['flight_name'] = ['no_matching_name']
                    self.flights_folders[i]['height'] = '0m' # update to metadata image height

            logging.info("Matching of flight folders with output paths completed successfully.")
        except Exception as e:
            logging.error(f"Error in matching flight folders: {e}")
    
    def refresh(self):
        try:
            self.__init__(self.input_path, self.output_path, self.data_overview_file, self.flight_log_file)
            logging.info("The state has been refreshed.")
        except Exception as e:
            logging.error(f"Error in refresh: {e}")

    def print_summary(self):
        for i, flight in enumerate(self.flights_folders):
            logging.info(f"{i}. Move: {flight['dir_name']:55} to location: {flight['output_path']}")

    def summary(self):
        try:
            self.get_information()
            self.reflectance_logic_with_timestamps()
            self.detect_and_handle_new_routes()
            self.match()

            while True:
                self.print_summary()
                edit = input("Do you want to edit any output paths? (yes/no): ").strip().lower()
                if edit in ['yes', 'y']:
                    self._edit_paths()
                else:
                    break
        except Exception as e:
            logging.error(f"Error in summary: {e}")

    def _edit_paths(self):
        try:
            type_edit = input("Do you want to move, duplicate, trash or move to skyline folder? (move/duplicate/trash/skyline)").strip().lower()
            if type_edit in ['move', 'm']:
                self._move_path()
            elif type_edit in ['duplicate', 'd']:
                self._duplicate_path()
            elif type_edit in ['trash', 't']:
                self._trash_path()
            elif type_edit in ['skyline','s']:
                self._skyline_path()
        except Exception as e:
            logging.error(f"Error editing paths: {e}")

    def _move_path(self):
        try:
            flight_index = int(input("Enter the number corresponding to the flight you want to edit: "))
            new_path_index = int(input("Enter the number corresponding to the flight whose path you want to use: "))
            if 0 <= flight_index < len(self.flights_folders) and 0 <= new_path_index < len(self.flights_folders):
                self.flights_folders[flight_index]['output_path'] = self.flights_folders[new_path_index]['output_path']
                logging.info(f"Updated: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[flight_index]['output_path']}")
            else:
                logging.warning("Invalid indices entered. Please try again.")
        except ValueError:
            logging.error("Invalid input. Please enter numbers corresponding to the flight indices.")

    def _duplicate_path(self):
        try:
            flight_index = int(input("Enter the number corresponding to the flight you want to duplicate: "))
            new_path_index = int(input("Enter the number corresponding to the flight whose path you want to use: "))
            if 0 <= flight_index < len(self.flights_folders) and 0 <= new_path_index < len(self.flights_folders):
                temp = copy.deepcopy(self.flights_folders[flight_index])
                temp['output_path'] = self.flights_folders[new_path_index]['output_path']
                self.flights_folders.append(temp)
                logging.info(f"Duplicated: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[-1]['output_path']}")
            else:
                logging.warning("Invalid indices entered. Please try again.")
        except ValueError:
            logging.error("Invalid input. Please enter numbers corresponding to the flight indices.")

    def _trash_path(self):
        try:
            flight_index = int(input("Enter the number corresponding to the flight you want to trash: "))
            if 0 <= flight_index < len(self.flights_folders):
                info = self.data_overview.loc[self.data_overview['FlightRoute'] == self.flights_folders[flight_index]['flight_name'][0]]
                output_path = os.path.join(self.output_path, '_TRASHCAN\\'+ str(info['BasePath'].values[0]), f"{self.flights_folders[flight_index]['date']} {str(info['BaseName'].values[0])} {str(info['BaseDrone'].values[0])} {str(info['BaseHeight'].values[0])} {str(info['BaseType'].values[0])} {str(info['BaseOverlap'].values[0])}")
                self.flights_folders[flight_index]['output_path'] = output_path
                self.flights_folders[flight_index]['flight_name'] = [f"{self.flights_folders[flight_index]['flight_name'][0]}_trashed-flight"]
                logging.info(f"Trashed: {self.flights_folders[flight_index]['dir_name']} to new location: {self.flights_folders[flight_index]['output_path']}")
            else:
                logging.warning("Invalid indices entered. Please try again.")
        except ValueError:
            logging.error("Invalid input. Please enter numbers corresponding to the flight indices.")

    def _skyline_path(self):
        try:
            flight_index = int(input("Enter the number corresponding to the flight you want to move to skyline: "))
            if 0 <= flight_index < len(self.flights_folders):
                info = self.data_overview.loc[self.data_overview['FlightRoute'] == self.flights_folders[flight_index]['flight_name'][0]]
                output_path = os.path.join(self.output_path, '_SKYLINE\\'+ str(info['BasePath'].values[0]), f"{self.flights_folders[flight_index]['date']} {str(info['BaseName'].values[0])} {str(info['BaseDrone'].values[0])} {str(info['BaseHeight'].values[0])} {str(info['BaseType'].values[0])} {str(info['BaseOverlap'].values[0])}")
                self.flights_folders[flight_index]['output_path'] = output_path
                self.flights_folders[flight_index]['flight_name'] = [f"{self.flights_folders[flight_index]['flight_name'][0]}_trashed-flight"]
                logging.info(f"Moved to skyline: {self.flights_folders[flight_index]['dir_name']} to location: {self.flights_folders[flight_index]['output_path']}")
            else:
                logging.warning("Invalid index entered. Please try again.")
        except Exception as e:
            logging.error(f"Error in _skyline_path: {e}")

    @staticmethod
    def move_directory(source_path: str, destination_path: str):
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            command = f'xcopy "{source_path}\\*" "{destination_path}\\" /E /I /Y'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error copying {source_path} to {destination_path}: {result.stderr}")
            else:
                logging.info(f"Completed moving directory {source_path} to {destination_path}")
        except Exception as e:
            logging.error(f"Exception moving {source_path} to {destination_path}: {e}")

    def move_files_to_output(self):
        total_folders = len(self.flights_folders)
        q = Queue()
        threads = []

        pbar = tqdm(total=total_folders, desc="Moving directories", unit="dir")

        def worker():
            while not q.empty():
                source_path, destination_path = q.get()
                self.move_directory(source_path, destination_path)
                pbar.update(1)
                q.task_done()

        for flight in self.flights_folders:
            source_path = os.path.join(self.input_path, flight['dir_name'])
            destination_path = os.path.join(flight['output_path'], flight['dir_name'])
            q.put((source_path, destination_path))

        for _ in range(min(10, total_folders)):
            t = Thread(target=worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        pbar.close()
        self._save_flight_log()
        

    def _save_flight_log(self):
        
        try:
            df = pd.read_csv(self.temp_log_file)
            df['start_time'] = df['start_time'].astype(int)
            df['end_time'] = df['end_time'].astype(int)
            #logging.info(f"initial csv {df}")

            for flight in self.flights_folders:
                    #logging.info(f'to {flight}')
                    dir_name = flight['dir_name']
                    flight_name = str(flight['flight_name'][0])
                    date = flight['date']
                    folder_ID = flight['folder_ID']
                    # Explicitly convert start_time and end_time to integers
                    start_time = int(flight['start_time'])
                    end_time = int(flight['end_time'])
                    flight_type = flight['type']
                    num_files = str(flight['num_files'])
                    num_dir = 1
                    output_path = flight['output_path']
                    height = flight['height']
                    # Find existing entry with the same date and flight name
                    
                    # Assuming 'date' should be treated as a string for comparison
                    existing_entry = df[(df['date'].astype(str) == str(date)) & (df['flight_name'].astype(str) == str(flight_name))]

                    #logging.info(existing_entry)
                    if not existing_entry.empty:
                        # Update existing entry
                        idx = existing_entry.index[0]
                        df.at[idx, 'start_time'] = min(df.at[idx, 'start_time'], start_time)
                        df.at[idx, 'end_time'] = max(df.at[idx, 'end_time'], end_time)

                        df.at[idx, 'dir_name'] += f", {dir_name}"
                        df.at[idx, 'folder_ID'] += f", {folder_ID}"
                        df.at[idx, 'type'] += f", {flight_type}"
                        df.at[idx, 'num_files'] += f", {num_files}"
                        df.at[idx, 'num_dir'] += num_dir

                        # Compare and update start_time and end_time
                    else:
                        # Add new entry
                        new_entry = {
                            "dir_name": dir_name,
                            "flight_name": flight_name,
                            "date": date,
                            "folder_ID": folder_ID,
                            "start_time": start_time,
                            "end_time": end_time,
                            "type": flight_type,
                            "num_files": num_files,
                            "num_dir": num_dir,
                            "output_path": output_path,
                            "height": height
                        }
                        new_entry = pd.DataFrame([new_entry])
                        df = pd.concat([df,new_entry], ignore_index=True)

            df.to_csv(self.temp_log_file, index=False)
            self._load_flight_log(self.temp_log_file)
            logging.info("Flight log saved successfully.")
        except Exception as e:
            logging.error(f"Error saving flight log: {e}")


    def update_main_csv(self):
        try:
            temp_log = self._load_flight_log(self.temp_log_file)
            main_log = self._load_flight_log(self.flight_log_file)
            #---------------------------
            # test can be preformed here
            #---------------------------
            new_log = pd.concat([main_log,temp_log],ignore_index=True)
            new_log.to_csv(self.flight_log_file, index=False)

            logging.info("Main flight log updated successfully.")
        except Exception as e:
            logging.error(f"Error updating main flight log: {e}")

    def _close_and_wipe_sd_cards(self):
        try:
            shutil.rmtree(self.input_path)
            logging.info("SD card wiped successfully.")
        except Exception as e:
            logging.error(f"Error wiping SD card: {e}")


if __name__ == "__main__":
    def detect_sd_cards() -> List[str]:
        potential_paths = ["G:/DCIM", "I:/DCIM", "D:/DCIM"]
        available_paths = [path for path in potential_paths if os.path.exists(path)]
        return available_paths

    output_path = "P:\\PhenoCrop\\1_flights"
    data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
    flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"

    sd_card_paths = detect_sd_cards()
    logging.info(f'SD cards detected: {sd_card_paths}')

    file_transfers = [FileTransfer(input_path=sd_card_path, output_path=output_path, data_overview_file=data_file, flight_log=flight_log) for sd_card_path in sd_card_paths]



    for ft in file_transfers:
        ft.summary()
        

    move = input('Do you want to move the files? (yes/no): ').strip().lower()
    if move in ['yes', 'y']:
        for ft in file_transfers:
            logging.info('simulating moving the files')
            ft.move_files_to_output()

        logging.info('Files moved successfully')
        final_user_input = input("Do you want to add flight to flight log?(yes/no)").strip().lower()
        if final_user_input in ['yes', 'y']:
            ft.update_main_csv()
            laast = input("do you waant to wipe the sd cards?(yes/no)").strip().lower()
            if laast in ['yes', 'y']:
                for ft in file_transfers:
                    ft._close_and_wipe_sd_cards()

        
