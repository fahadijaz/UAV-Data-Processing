from filetransfer import FileTransfer
import os
import csv
import pandas as pd

input_path = "P:\\PhenoCrop\\1_flights"
data_file = "P:\\PhenoCrop\\0_csv\\data_overview.csv"
flight_log = "P:\\PhenoCrop\\0_csv\\flight_log.csv"
output_path = "P:\\PhenoCrop\\1_flights"
not_logged_csv_path = "P:\\PhenoCrop\\Test_Folder\\Test_ISAK\\not_logged.csv"
original_df = pd.read_csv(not_logged_csv_path)


folder_list = os.listdir(input_path) #main folder
print(folder_list)
not_logged_flights = []
for field in folder_list:
    if field != '_TRASHCAN' and field != 'skyline' and field != 'PILOT':
        all_folder_path = os.path.join(input_path,field,'3D')
        for folder in os.listdir(all_folder_path):
            try:
                if folder != 'Thumb.db':
                    folder_path = os.path.join(all_folder_path, folder)
                    folder_obj = FileTransfer(folder_path,output_path,data_overview_file=data_file, flight_log=flight_log)
                    folder_obj.get_information()
                    folder_obj.test_folder_for_TIF()
                    folder_obj.reflectance_types()
                    folder_obj.detect_and_handle_new_routes()
                    folder_obj.match()
                    folder_obj.save_flight_log()
            except Exception as e:
                not_logged_flights.append([folder,folder_path])

df = pd.DataFrame(columns=['folder','path'])
df = pd.DataFrame(not_logged_flights, columns=['folder','path'])
df = pd.concat([original_df, df], ignore_index=True)
df.to_csv(not_logged_csv_path, index=False)