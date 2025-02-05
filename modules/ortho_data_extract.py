from ortho_data_extract_funct import precise_timing_decorator
from file_system_functions import find_files_in_folder


import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
import os
import logging
from rasterstats import zonal_stats

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def ensure_crs_alignment(gdf, raster_crs):
    """
    Ensures that the GeoDataFrame has the same CRS as the raster.

    Parameters:
        gdf (GeoDataFrame): Geospatial dataframe containing vector geometries.
        raster_crs (CRS): Coordinate reference system of the raster.

    Returns:
        GeoDataFrame: CRS-aligned GeoDataFrame.
    """
    try:
        if gdf.crs != raster_crs:
            logging.warning("CRS mismatch detected. Reprojecting shapefile to match raster CRS.")
            gdf = gdf.to_crs(raster_crs)
    except Exception as e:
        logging.error(f"Error while aligning CRS: {e}")
        raise
    return gdf


def compute_additional_statistics(values):
    """
    Computes additional statistics manually, such as variance, skewness, and percentiles.

    Parameters:
        values (array-like): List or array of raster values.

    Returns:
        dict: Dictionary of computed statistics.
    """
    try:
        if len(values) == 0:
            return {stat: np.nan for stat in [
                "variance", "cv", "skewness", "kurtosis", "variety",
                "top_10", "top_15", "top_20", "top_25", "top_35", "top_50", "q25", "q75", "iqr"
            ]}
        
        unique_vals = np.unique(values)

        return {
            "variance": np.nanvar(values),
            "cv": np.nanstd(values) / np.nanmean(values) if np.nanmean(values) != 0 else np.nan,
            "skewness": pd.Series(values).skew(),
            "kurtosis": pd.Series(values).kurtosis(),
            "variety": len(unique_vals),
            "top_10": np.nanpercentile(values, 90),
            "top_15": np.nanpercentile(values, 85),
            "top_20": np.nanpercentile(values, 80),
            "top_25": np.nanpercentile(values, 75),
            "top_35": np.nanpercentile(values, 65),
            "top_50": np.nanpercentile(values, 50),
            "q25": np.nanpercentile(values, 25),
            "q75": np.nanpercentile(values, 75),
            "iqr": np.nanpercentile(values, 75) - np.nanpercentile(values, 25)
        }

    except Exception as e:
        logging.error(f"Error computing additional statistics: {e}")
        return {stat: np.nan for stat in [
            "variance", "cv", "skewness", "kurtosis", "variety",
            "top_10", "top_15", "top_20", "top_25", "top_35", "top_50", "q25", "q75", "iqr"
        ]}


def extract_raster_stats_multiple(shp, raster_paths, project_name, flight, plot_geom="none"):
    """
    Extracts raster statistics for multiple raster files and appends results to a DataFrame.

    Parameters:
        shp (str): Path to GeoJSON or shapefile containing geometries.
        raster_paths (dict): Dictionary of raster names and their file paths.
        project_name (str): Project name.
        flight (str): Flight name.
        plot_geom (str, optional): Plot geometry option. Default is "none".

    Returns:
        pd.DataFrame: DataFrame with extracted raster statistics for each raster.
    """

    logging.info(f"Processing project: {project_name}, Flight: {flight}")
    logging.info(f"Reading shapefile: {shp}")

    # Validate shapefile existence
    if not os.path.exists(shp):
        logging.error(f"Shapefile not found: {shp}")
        raise FileNotFoundError(f"Shapefile not found: {shp}")

    try:
        gdf = gpd.read_file(shp)
        if gdf.empty:
            logging.error("Shapefile contains no geometries!")
            raise ValueError("Shapefile is empty.")
        
        gdf.columns = gdf.columns.str.lower()  # Convert column names to lowercase
    except Exception as e:
        logging.error(f"Error reading shapefile: {e}")
        raise

    all_results = []

    for raster_name, raster_path in raster_paths.items():
        logging.info(f"Processing raster: {raster_name} ({raster_path})")

        # Validate raster file existence
        if not os.path.exists(raster_path):
            logging.error(f"Raster file not found: {raster_path}")
            continue  # Skip missing rasters instead of stopping execution

        try:
            with rasterio.open(raster_path) as src:
                gdf = ensure_crs_alignment(gdf, src.crs)

                # Extract zonal statistics
                stats = zonal_stats(
                    gdf, raster_path,
                    stats=["count", "sum", "mean", "median", "std", "min", "max", "range", "majority", "minority", "unique"],
                    raster_out=True  # Extract pixel values for additional stats
                )
            
            # Extract raw values for additional calculations
            raw_values = [
                stat["mini_raster_array"].compressed() if "mini_raster_array" in stat else np.array([])
                for stat in stats
            ]

            # Compute additional statistics
            additional_stats = [compute_additional_statistics(vals) for vals in raw_values]

            # Convert to DataFrame
            df_stats = pd.DataFrame(stats).drop(columns=["mini_raster_array"], errors="ignore")
            df_additional = pd.DataFrame(additional_stats)

            # Merge both dataframes
            df = pd.concat([df_stats, df_additional], axis=1)
            df.columns = [f"{raster_name}_{col}" for col in df.columns]  # Prefix columns
            df.insert(0, "geometry", gdf.geometry)
            df.insert(1, "project", project_name)
            df.insert(2, "flight", flight)

            all_results.append(df)

            logging.info(f"Successfully processed raster: {raster_name}")

        except Exception as e:
            logging.error(f"Error processing raster {raster_name}: {e}")
            continue  # Skip this raster and move to the next one

    # Merge all results
    if not all_results:
        logging.error("No raster statistics could be extracted.")
        return pd.DataFrame()  # Return empty DataFrame if no data

    final_df = pd.concat(all_results, axis=1).loc[:, ~pd.concat(all_results, axis=1).columns.duplicated()]

    logging.info("Processing complete! Returning final DataFrame.")
    return final_df

# # Example Usage
src_folder = r'D:\PhenoCrop\2_pix4d_cleaned\PHENO_CROP\MS\20240619 PHENO_CROP P4M 20m MS 70 75\2_Orthomosaics'
paths = find_files_in_folder(src_folder, 'tif')
raster_files = {
    "red": next((tif for tif in paths if "red_red" in tif), None),
    "blue": next((tif for tif in paths if "blue_blue" in tif), None),
    "green": next((tif for tif in paths if "green_green" in tif), None),
    "nir": next((tif for tif in paths if "nir_nir" in tif), None),
    "red_edge": next((tif for tif in paths if "red_edge_red_edge" in tif), None)
}

shapefile_path = r"D:\PhenoCrop\3_qgis\3_Extraction Polygons\3. FINAL MASKS PYTHON\24 PHENO_CROP Avlingsregistrering_sorted_ID_polygons_shrinked.geojson"  # Replace with the path to your GeoJSON file

project = "PHENO_CROP"
flight = "20240619 PHENO_CROP P4M 20m MS 70 75"

stats_df = extract_raster_stats_multiple(shapefile_path, raster_files, project, flight)
print(stats_df.head())  # View the extracted statistics






# @precise_timing_decorator
# def plot_orthomosaic_with_geojson(tif_path, geojson_path):
#     """Reads and plots an orthomosaic GeoTIFF with a GeoJSON overlay using plot()."""
    
#     # Open the TIFF file with rasterio
#     with rasterio.open(tif_path) as src:
#         # Read the raster data (assuming the first three bands are RGB)
#         img_data = src.read([1, 2, 3])  # Reading the RGB bands (adjust if more bands exist)
#         img_data = img_data.transpose(1, 2, 0)  # Reorder to (height, width, channels)

#         # Create the plot
#         fig, ax = plt.subplots(figsize=(10, 10))

#         # Plot the orthomosaic image with matplotlib
#         # Using rasterio's show to display the image as a background
#         show(src, ax=ax, title="Orthomosaic with GeoJSON Overlay", adjust='box')

#         # Load GeoJSON with geopandas
#         shapefile = gpd.read_file(geojson_path)
#         shapefile.columns = shapefile.columns.str.lower() # convert all column names in the GeoDataFrame to lowercase
#         # Check CRS of the GeoJSON and reproject if necessary
#         if shapefile.crs != src.crs:
#             print(f"Reprojecting GeoJSON to match raster CRS: {src.crs}")
#             shapefile = shapefile.to_crs(src.crs)
        
#         # Print the bounds for debugging
#         print("Raster bounds:", src.bounds)
#         print("GeoJSON bounds:", shapefile.total_bounds)

#         # Plot the GeoJSON overlay on top of the orthomosaic
#         shapefile.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=0.5)  # Plot boundaries
        
#         # # Optionally, fill the polygons with a transparent color
#         # shapefile.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2)
        
#         # Show the plot
#         plt.xlabel("Longitude")
#         plt.ylabel("Latitude")
#         plt.show()

# # Example usage
# tif_path = r'D:\PhenoCrop\3_orthomosaics_rgb_ndvi\PHENO_CROP\RGB\20240718 PHENO_CROP M3M 30m MS 70 75_transparent_mosaic_group1_25%.tif'
# geojson_path = r"D:\PhenoCrop\3_qgis\3_Extraction Polygons\3. FINAL MASKS PYTHON\24 PHENO_CROP Avlingsregistrering_sorted_ID_polygons_shrinked.geojson"  # Replace with the path to your GeoJSON file

# plot_orthomosaic_with_geojson(tif_path, geojson_path)



# # Find out the resolution of the source file
# import rasterio
# with rasterio.open(tif_path) as src:
#     print("Resolution of the orthomosaic:", src.res)
    
# # # Verify that each raster in raster_paths has valid metadata, including bounds and CRS.
# # for band, path in raster_paths.items():
# #     with rasterio.open(path) as src:
# #         print(f"Checking {band}: Bounds={src.bounds}, CRS={src.crs}")

# def clean_and_sort_imports(import_list):
#     """Removes duplicate imports and sorts them by length."""
#     unique_imports = sorted(set(import_list), key=len)
#     return unique_imports