from filetransfer import FileTransfer
import os
import csv

input_path = "P:\\PhenoCrop\\1_flights"
data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"
output_path = "P:\\PhenoCrop\\1_flights"

folder_list = os.listdir(input_path) #main folder
print(folder_list)
not_logged_flights = []
for field in folder_list:
    if field != 'E166' and field != '_TRASHCAN':
        all_folder_path = os.path.join(input_path,field,'3D')
        for folder in os.listdir(all_folder_path):
            try:
                folder_path = os.path.join(all_folder_path, folder)
                folder_obj = FileTransfer(folder_path,output_path,data_overview_file=data_file, flight_log=flight_log)
                folder_obj.get_information()
                folder_obj.test_folder_for_TIF()
                folder_obj.reflectance_types()
                folder_obj.detect_and_handle_new_routes()
                folder_obj.match()
                folder_obj.save_flight_log()
            except Exception as e:
                not_logged_flights.append(f'could not log folder with name: {folder}, and path{folder_path}')
not_logged_flights

with open("P:\\PhenoCrop\\Test_Folder\\Test_ISAK\\not_logged.csv", 'w') as f:
     
    # using csv.writer method from CSV package
    write = csv.writer(f)
    write(not_logged_flights)