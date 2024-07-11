from filetransfer import FileTransfer
import os

input_path = "P:\\PhenoCrop\\1_flights"
data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"

folder_list = os.listdir(input_path) #main folder
print(folder_list)
for field in folder_list:
    if field != 'E166' and field != '_TRASHCAN':
        all_folder_path = os.path.join(input_path,field,'MS')
        for folder in os.listdir(all_folder_path):
            folder_path = os.path.join(all_folder_path, folder)
            folder_obj = FileTransfer(folder_path,data_overview_file=data_file, flight_log=flight_log)
            folder_obj.get_information()
            folder_obj.test_folder_for_TIF()
            folder_obj.reflectance_types()
            folder_obj.detect_and_handle_new_routes()
            folder_obj.match()
            folder_obj.save_flight_log()

