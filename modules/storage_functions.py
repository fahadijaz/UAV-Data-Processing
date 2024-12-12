import os

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def measure_folders_size(folders_dict):
    folder_sizes = {}
    for folder_name, folder_info in folders_dict.items():
        folder_path = folder_info[0]
        size_in_bytes = get_folder_size(folder_path)
        size_in_gb = size_in_bytes / (1024 ** 3)  # Convert bytes to GB
        folder_sizes[folder_name] = size_in_gb
        print(folder_name, ": ", size_in_gb, "GB")
    return folder_sizes

# # Example usage
# folders_dict = {
#     "Documents": ["/path/to/documents"],
#     "Pictures": ["/path/to/pictures"],
#     "Music": ["/path/to/music"]
# }

# folder_sizes = measure_folders_size(folders_dict)
# import pprint

# # Prints the nicely formatted dictionary
# pprint.pprint(folder_sizes)

import os

def count_files_with_extension(folder_path, extension):
    count = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            if f.endswith(extension):
                count += 1
    return count

def count_files_in_folders(folders_dict, extension):
    file_counts = {}
    for folder_name, folder_info in folders_dict.items():
        folder_path = folder_info[0]
        file_counts[folder_name] = count_files_with_extension(folder_path, extension)
        print(Folder_name, ": ", file_counts[folder_name], "JPG Images")
    return file_counts

# # Example usage
# folders_dict = {
#     "Documents": ["/path/to/documents"],
#     "Pictures": ["/path/to/pictures"],
#     "Music": ["/path/to/music"]
# }

# extension = ".txt"
# file_counts = count_files_in_folders(folders_dict, extension)
# print(file_counts)
