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
# Counting with a list of extensinos

def count_files_with_extensions(folder_path, extensions):
    counts = {ext: 0 for ext in extensions}
    total_count = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            for ext in extensions:
                if f.lower().endswith(ext.lower()):
                    counts[ext] += 1
                    total_count += 1
    counts["total"] = total_count
    return counts

def count_files_in_folders(folders_dict, extensions):
    file_counts = {}
    for folder_name, folder_info in folders_dict.items():
        folder_path = folder_info[0]
        counts = count_files_with_extensions(folder_path, extensions)
        file_counts[folder_name] = counts
        print(folder_name, ": ", file_counts[folder_name], "Images")
    return file_counts

# # Example usage
# folders_dict = {
#     "Documents": ["/path/to/documents"],
#     "Pictures": ["/path/to/pictures"],
#     "Music": ["/path/to/music"]
# }

# extensions = [".txt", ".pdf", ".docx"]
# file_counts = count_files_in_folders(folders_dict, extensions)
# print(file_counts)