import glob
from extraction_polygons_funct import *
from file_system_functions import find_files_in_folder

source_folder_sowing_geojson = r"sowing"
output_subfolder = "extraction"

#SIMPLE UNIQUE ID SYSTEM WITH START, ENF AND COLUMN STEP
metadata_keys = ["field", "id_start", "id_end", "step", "width", "height", "rotation_polygons", "rotation_grid_for_ordering"]
conditions = {
    "PhenoCrop": ("PhenoCrop", 100, 196, 100, 9.5, 2.1, 12, -23),
    "Frontier": ("Frontier", 100, 111, 100, 9.5, 2.1, 12, -23),
    "Gene2Bread": ("Gene2Bread", 100, 126, 100, 9.5, 2.1, 12, -23),
    "Diversity": ("Diversity", 132, 100, -1, 2, 2, 12, -23), # ID End does not work due to unusual design
    "ProteinBar Vollebekk": ("ProteinBar Vollebekk", 1100, 1121, 100, 13, 2.1, 28, -46.5),
    "ProteinBar NAPE": ("ProteinBar NAPE", 101, 120, 100, 13.25, 2, 28, -46.5), # Dont have the sowing shape files for this field. Generated the centroids menually
    "E166": ("E166", 1, 13, 0, 13, 3, 113, -116), # The original sowing shape files not found. These are based on the manually shrinked polygons created by students in 2024.
                                                    # The ID Logic is tricky for this one
    "Soraas": ("Soraas", 101000, 101085, 1000, 9.5, 2.1, 67, -78),
}

sowing_files = find_files_in_folder(source_folder_sowing_geojson, 'geojson')
metadata_dict = create_metadata_based_on_filename(sowing_files, conditions, metadata_keys)

for file_path, variables in metadata_dict.items():
    input_file = file_path
    # Declare variables for each metadata field
    for var_name, value in variables.items():
        globals()[var_name] = value
    file_path, field, id_start, id_end, step, width, height, rotation_polygons, rotation_grid_for_ordering

    # Naming the input and output files
    # Generate centroids
    output_cenroids = modify_filename(input_file, "1_", "_centroids", output_subfolder)
    # Reorder the centroids
    input_centroids = output_cenroids
    output_ordered_centroids = modify_filename(input_file, "2_", "_centroids_ordered", output_subfolder)
    # Update the IDs
    input_ordered_centroids = output_ordered_centroids
    output_centroids_with_IDs = modify_filename(input_file, "3_", "_centroids_IDs", output_subfolder)
    # Generate the shrinked polygons
    input_centroids_with_IDs = output_centroids_with_IDs
    output_extraction_polygons = modify_filename(input_file, "4_", "_polygons_shrinked", output_subfolder)


    # Performing the centroid operations
    polygons_to_centroids(input_file, output_cenroids) # Find the centroid of the sowing polygons
    reorder_points_by_columns(input_centroids, output_ordered_centroids, rotation_grid_for_ordering)  # Reorder the centroids. Adjust rotation_angle as needed
    update_ids(input_ordered_centroids, output_centroids_with_IDs, id_start, id_end, step)  # Update the IDs


    # Generate the shrinked polygons
    generate_shrinked_polygons(input_centroids_with_IDs,
                                output_extraction_polygons,
                                width,
                                height,
                                rotation_polygons)