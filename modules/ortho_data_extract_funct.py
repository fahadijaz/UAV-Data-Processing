from file_system_functions import find_files_in_folder

import os
import gc
import re
import csv
import math
import time
import glob
import rasterio
import itertools
import cupy as cp
import numpy as np
import pandas as pd
from numba import njit
import geopandas as gpd
import concurrent.futures
from rasterio.plot import show
from collections import Counter
import matplotlib.pyplot as plt
from shapely.geometry import box
import cupy as cp  # GPU acceleration
from rasterio.enums import Resampling
import psutil  # To monitor memory usage
from rasterio.transform import from_origin
from rasterio.features import geometry_mask

def add_suffix_to_file_name(file_path, suffix):
    """
    Adds a suffix to the file name in the given file path.
    
    Parameters:
    - file_path (str): The original file path.
    - suffix (str): The suffix to add to the file name (before the file extension).
    
    Returns:
    - str: The updated file path with the suffix added to the file name.
    """
    # Separate the directory, file name, and extension
    directory, file_name = os.path.split(file_path)
    base_name, ext = os.path.splitext(file_name)
    
    # Add the suffix to the file name
    new_file_name = f"{base_name}{suffix}{ext}"
    
    # Reconstruct the full file path
    new_file_path = os.path.join(directory, new_file_name)
    return new_file_path


def downscale_image(file_path, output_folder, scale_factor):
    """
    Downscale a TIFF/JPG file and save it in the structured output directory.

    Parameters:
        file_path (str): The path to the original file.
        output_folder (str): The base output folder.
        scale_factor (float): Scaling factor (e.g., 0.25 for 25%).

    Returns:
        str: Path to the saved downscaled file.
    """
    print(f"\n⚙️ Processing: {os.path.basename(file_path)} at {int(scale_factor * 100)}% resolution")

    try:
        with rasterio.open(file_path) as src:
            # Compute new dimensions
            new_width = int(src.width * scale_factor)
            new_height = int(src.height * scale_factor)
            print(f"   - Original size: {src.width} x {src.height}")
            print(f"   - New size: {new_width} x {new_height}")

            # Read and resample image
            resampled_array = src.read(
                out_shape=(src.count, new_height, new_width),
                resampling=Resampling.bilinear
            )

            # Update metadata
            profile = src.profile
            profile.update(
                width=new_width,
                height=new_height,
                transform=src.transform * src.transform.scale(
                    (src.width / new_width), (src.height / new_height)
                )
            )


            # Save downscaled image
            print(f"   - Saving downscaled file: {output_folder}")
            with rasterio.open(output_folder, "w", **profile) as dst:
                dst.write(resampled_array)

            print(f"✅ Successfully downscaled: {os.path.basename(file_path)}")
            return output_folder

    except Exception as e:
        print(f"❌ ERROR processing {file_path}: {str(e)}")
        return None
    

## Timing Decorator
# A decorator (wrapper function) that logs the time taken for any function it wraps.
# To measure execution time of a function

def timing_decorator(func):
    """Decorator to measure execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start time
        result = func(*args, **kwargs)
        end_time = time.time()  # End time
        elapsed_time = end_time - start_time
        print(f"⏳ Execution time of {func.__name__}: {elapsed_time:.4f} seconds")
        return result
    return wrapper

## Using time.perf_counter() (More Precise)
# This is more precise than time.time() because perf_counter() accounts for system sleep time.

def precise_timing_decorator(func):
    """Decorator for high-precision execution timing."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"⏳ Execution time of {func.__name__}: {end_time - start_time:.6f} seconds")
        return result
    return wrapper

@precise_timing_decorator
def calculate_band_statistics(band_array, geom, transform):
    """Computes multiple statistics for raster values within a given geometry."""
    STATISTICS_LIST = [
                    "count", "sum", "mean", "median", "std", "min", "max", "range", "minority",
                    "majority", "variety", "variance", "cv", "skewness", "kurtosis", "top_10", 
                    "top_15", "top_20", "top_25", "top_35", "top_50", "q25", "q75", "iqr"
                    ]

    # Ensure band_array is 2D
    if band_array.ndim != 2:
        raise ValueError("band_array must be a 2D array (height × width).")
    
    # Create a mask for the geometry
    mask = geometry_mask([geom], transform=transform, invert=True, out_shape=band_array.shape)

    if np.sum(mask) == 0:  # Check if any pixels were selected
        print(f"Warning: No valid pixels found for geometry {geom}")
        print(f"Mask unique values: {np.unique(mask)}")  # Should contain both True & False
        return {stat: np.nan for stat in STATISTICS_LIST}  # Return NaNs

    masked_values = band_array[mask]

    if masked_values.size == 0:
        print(f"Warning: All pixels are masked for geometry {geom}")
        print(f"Masked pixel values: {masked_values}")
        return {stat: np.nan for stat in STATISTICS_LIST}

    if masked_values.size == 0:
        return {stat: np.nan for stat in [
            "count", "sum", "mean", "median", "std", "min", "max", "range", "minority",
            "majority", "variety", "variance", "cv", "skewness", "kurtosis", "top_10", 
            "top_15", "top_20", "top_25", "top_35", "top_50", "q25", "q75", "iqr"
        ]}
    
    # Compute statistics    
    unique_vals, counts = np.unique(masked_values, return_counts=True)
    majority = unique_vals[np.argmax(counts)] if unique_vals.size > 0 else np.nan
    minority = unique_vals[np.argmin(counts)] if unique_vals.size > 0 else np.nan

    return {
        "count": masked_values.size,
        "sum": np.nansum(masked_values),
        "mean": np.nanmean(masked_values),
        "median": np.nanmedian(masked_values),
        "std": np.nanstd(masked_values),
        "min": np.nanmin(masked_values),
        "max": np.nanmax(masked_values),
        "range": np.nanmax(masked_values) - np.nanmin(masked_values),
        "minority": minority,
        "majority": majority,
        "variety": len(unique_vals),
        # Variance – Measures how spread out the values are.
        "variance": np.nanvar(masked_values),
        # Coefficient of Variation (CV) – Standard deviation divided by the mean (useful for comparing variability).
        "cv": np.nanstd(masked_values) / np.nanmean(masked_values) if np.nanmean(masked_values) != 0 else np.nan,
        # Skewness – Measures asymmetry of the distribution (negative = left-skewed, positive = right-skewed).
        "skewness": pd.Series(masked_values).skew(),
        # Kurtosis – Measures how peaked or flat the distribution is compared to a normal distribution.
        "kurtosis": pd.Series(masked_values).kurtosis(),
        "top_10": np.nanpercentile(masked_values, 90), # Top 10% of values
        "top_15": np.nanpercentile(masked_values, 85), # Top 15% of values
        "top_20": np.nanpercentile(masked_values, 80), # Top 20% of values
        # If you want high reflectance areas (e.g., bright areas), you'd analyze top 25% values
        "top_25": np.nanpercentile(masked_values, 75), # Top 25% of values
        "top_35": np.nanpercentile(masked_values, 65), # Top 35% of values
        "top_50": np.nanpercentile(masked_values, 50), # Top 50% of values
        # 25th Percentile (Q1) – First quartile, representing the lower 25% of values.
        # If you're looking for areas with low vegetation index (NDVI), you might analyze Q1 values.
        "q25": np.nanpercentile(masked_values, 25),
        # 75th Percentile (Q3) – Third quartile, representing the upper 25% of values.
        "q75": np.nanpercentile(masked_values, 75),
         # Interquartile Range (IQR) – Difference between Q3 and Q1, showing spread without extreme values.
        "iqr": np.nanpercentile(masked_values, 75) - np.nanpercentile(masked_values, 25)
    }

def ensure_crs_alignment(shapefile, raster_crs):
    """Ensure the shapefile CRS matches the raster CRS."""
    if shapefile.crs != raster_crs:
        print(f"Reprojecting shapefile to match raster CRS: {raster_crs}")
        shapefile = shapefile.to_crs(raster_crs)
    return shapefile

FONT_STYLES = {
    "default": {
        "id_fontsize": 14,
        "id_fontweight": "normal",
        "id_fontcolor": "black",
        "id_fontfamily": "sans-serif",
        "id_bbox": False  # No bounding box
    },
    "bold_high_contrast": {
        "id_fontsize": 16,
        "id_fontweight": "bold",
        "id_fontcolor": "white",
        "id_fontfamily": "Arial",
        "id_bbox": {"facecolor": "black", "alpha": 0.7}  # Dark background for visibility
    },
    "large_minimal": {
        "id_fontsize": 18,
        "id_fontweight": "light",
        "id_fontcolor": "yellow",
        "id_fontfamily": "monospace",
        "id_bbox": None  # No bounding box
    },
    "compact_subtle": {
        "id_fontsize": 12,
        "id_fontweight": "medium",
        "id_fontcolor": "darkred",
        "id_fontfamily": "serif",
        "id_bbox": {"facecolor": "white", "alpha": 0.5}  # Light background for soft contrast
    }
}

# Function to plot with highlighted geometries based on their processing status
@precise_timing_decorator
def plot_with_highlighted_shp_geometry(shapefile, highlight_id, status, processed_ids, highlight_color='red', edgewidth=3, default_color='lightblue'):
    """
    Plots a GeoDataFrame with different colors for various stages of processing.
    
    Parameters:
    - shapefile (GeoDataFrame): The input GeoDataFrame containing geometries.
    - highlight_id (int or str): The ID of the geometry to highlight.
    - status (str): The processing status: 'processing', 'processed', or 'unprocessed'.
    - processed_ids (list): List of IDs of already processed polygons.
    - highlight_color (str): The color for the highlighted geometry's boundary. Default is 'red'.
    - edgewidth (float): The width of the boundary line for the highlighted geometry. Default is 3.
    - default_color (str): The default color for the other geometries. Default is 'lightblue'.
    """
    # Clear the current figure
    plt.clf()
    
    # Create a new figure   
    fig, ax = plt.subplots(figsize=(3, 3))

    # Plot the entire GeoDataFrame with different colors for processed and unprocessed geometries
    for idx, geom in shapefile.iterrows():
        # Check if the geometry has been processed
        if geom['id'] in processed_ids:
            color = 'green'  # Already processed
        elif geom['id'] == highlight_id:
            color = highlight_color  # Currently being processed
        else:
            color = default_color  # Unprocessed

        # Plot the individual geometry
        shapefile.loc[[idx]].plot(ax=ax, edgecolor='black', facecolor=color)

    # Set the title
    ax.set_title(f"Processing Plot #: {highlight_id}")

    # Display the plot
    plt.show()

@precise_timing_decorator
def plot_with_highlighted_ortho_geometry(
    shapefile, highlight_id, status, processed_ids, 
    ortho_path=None, highlight_color='khaki', edgewidth=0.25, 
    default_color='lightslategrey', opacity=0.4, 
    plot_size=(5, 5), show_ids=True, 
    zoom=True, zoom_out_factor=6, 
    font_style="bold_high_contrast",
    id_bbox = False, project_name = "None", flight = "None"
):

    """
    Plots a GeoDataFrame with different colors for various stages of processing.
    Optionally overlays the plot on an orthomosaic.
    
    Parameters:
    - shapefile (GeoDataFrame): The input GeoDataFrame containing geometries.
    - highlight_id (int or str): The ID of the geometry to highlight.
    - status (str): The processing status: 'processing', 'processed', or 'unprocessed'.
    - processed_ids (list): List of IDs of already processed polygons.
    - ortho_path (str, optional): Path to the orthomosaic GeoTIFF file.
    - highlight_color (str): Color for the highlighted geometry's boundary (default: 'red').
    - edgewidth (float): Width of the boundary line for the highlighted geometry (default: 3).
    - default_color (str): Default color for other geometries (default: 'lightblue').
    - opacity (float): Opacity level of the polygons (default: 0.5).
    - plot_size (tuple): Size of the plot in inches (default: (10, 10)).
    - show_ids (bool): Whether to display the polygon IDs inside the plot (default: True).
    - zoom (bool): Whether to zoom in on the highlighted geometry (default: True).
    - zoom_out_factor (float): Controls zoom-out level (default: 1.5, where 1 = exact bounds).
    - font_style (str): Preset style for ID text. Options:
        - "default": Standard black text with no background.
        - "bold_high_contrast": Large, bold white text with a black background.
        - "large_minimal": Large yellow text with no background.
        - "compact_subtle": Small, dark red text with a light background.
      (default: "default")
    - id_bbox (bool): Whether to show a white bounding box around ID text (default: False).

    """
    # Clear the current figure
    plt.clf()

    # Create a new figure with user-defined size
    fig, ax = plt.subplots(figsize=plot_size)

    # Plot the orthomosaic if provided
    if ortho_path:
        with rasterio.open(ortho_path) as src:
            show(src, ax=ax, title= f"Raster processing status for {project_name}", adjust='box')

            # Reproject the shapefile to match the orthomosaic CRS if necessary
            if shapefile.crs != src.crs:
                print(f"Reprojecting shapefile to match orthomosaic CRS: {src.crs}")
                shapefile = shapefile.to_crs(src.crs)

    # Set default zoom boundaries (entire dataset)
    minx, miny, maxx, maxy = shapefile.total_bounds  
    
    # If zoom is enabled, adjust bounds to zoom in on the highlighted geometry
    if zoom and highlight_id in shapefile['id'].values:
        highlight_geom = shapefile[shapefile['id'] == highlight_id].geometry.iloc[0]
        minx, miny, maxx, maxy = highlight_geom.bounds

        # Apply zoom out factor (expand bounds)
        width = maxx - minx
        height = maxy - miny
        minx -= width * (zoom_out_factor - 1) / 2
        maxx += width * (zoom_out_factor - 1) / 2
        miny -= height * (zoom_out_factor - 1) / 2
        maxy += height * (zoom_out_factor - 1) / 2

        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)

    # Plot each polygon with different colors based on processing status
    for idx, geom in shapefile.iterrows():
        if geom['id'] in processed_ids:
            color = 'green'  # Processed
        elif geom['id'] == highlight_id:
            color = highlight_color  # Currently processing
        else:
            color = default_color  # Unprocessed

        # Plot the individual geometry with opacity control
        shapefile.loc[[idx]].plot(ax=ax, edgecolor='black', facecolor=color, linewidth=edgewidth, alpha=opacity)

        # Get font settings from dictionary
        font_settings = FONT_STYLES.get(font_style, FONT_STYLES["default"])  # Default if not found
    
        # Extract font properties
        id_fontweight = font_settings["id_fontweight"]
        id_fontcolor = font_settings["id_fontcolor"]
        id_fontfamily = font_settings["id_fontfamily"]
        if id_bbox:
            id_bbox = font_settings["id_bbox"]

        # Adjust font color based on processing status
        if geom['id'] in processed_ids:
            id_fontcolor = 'lime'  # Processed
        elif geom['id'] == highlight_id:
            id_fontcolor = 'yellow'  # Being processed

        # Adjust font size based on the zoom level or polygon size
        if zoom:
            # Calculate font size based on the zoomed area
            area = (maxx - minx) * (maxy - miny)  # Area of the zoomed-in region
            id_fontsize = area ** 0.5 / 10  # Use square root of area for better scaling
            id_fontsize = max(15, min(20, id_fontsize))  # Limit font size to a reasonable range
        else:
            # Calculate font size based on the polygon size (width or height)
            width = maxx - minx
            height = maxy - miny
            area = width * height
            id_fontsize = area ** 0.5 / 10  # Square root of the area for proportionate size
            id_fontsize = max(10, min(20, id_fontsize))  # Limit font size to a reasonable range

        if show_ids:
            centroid = geom.geometry.centroid
            # Only print IDs that are within the zoomed/cropped area
            if not zoom or (minx <= centroid.x <= maxx and miny <= centroid.y <= maxy):
                ax.text(
                    centroid.x, centroid.y, str(geom['id']), 
                    fontsize=id_fontsize, fontweight=id_fontweight, 
                    color=id_fontcolor, family=id_fontfamily, 
                    ha='center', va='center',
                    bbox=id_bbox if id_bbox else None
                    )

    # Set the title
    ax.set_title(f"Processing Plot #: {highlight_id}" + "\n" +  f"for field {flight}", fontsize=14)

    # Display the plot
    plt.xlabel("Longitude", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.show()

@precise_timing_decorator
def process_rasters(shp, project_name, flight, green_raster_path, nir_raster_path, red_raster_path, \
                    rededge_raster_path, blue_raster_path, rgb_raster_thumb_path, \
                    stats_df, plot_geom = "none"):
    """Processes all geometries in the shapefile and calculates raster statistics."""
    # Open the blue raster separately if the path exists
    if blue_raster_path:
        blue = rasterio.open(blue_raster_path)
    else:
        blue = None
    
    with rasterio.open(red_raster_path) as red, \
         rasterio.open(green_raster_path) as green, \
         rasterio.open(nir_raster_path) as nir, \
         rasterio.open(rededge_raster_path) as rededge:

        # Ensure shapefile matches raster CRS
        shp_crs = ensure_crs_alignment(shp, red.crs)

        # Track processed polygons by ID
        processed_ids = []

        for i, geom in enumerate(shp_crs.geometry):

            start_time = time.time()  # Start timing before the loop

            print(f"Processing geometry {i + 1}/{len(shp_crs)} (ID: {shp_crs['id'][i]})")
            
            highlight_status = 'processing'
            
            if plot_geom == "ortho":
                # Plot the field ortho and highlight the current geometry being processed
                plot_with_highlighted_ortho_geometry(shp_crs, shp_crs.iloc[i]['id'], highlight_status, processed_ids, ortho_path=rgb_raster_thumb_path, project_name=project_name, flight=flight)
            elif plot_geom == "shp":
                # Plot the field plots and highlight the current geometry being processed
                plot_with_highlighted_shp_geometry(shp_crs, shp_crs.iloc[i]['id'], highlight_status, processed_ids, highlight_color='red', edgewidth=3, default_color='lightblue')

            # Read bands as float
            red_band = red.read(1).astype(float)
            green_band = green.read(1).astype(float)
            nir_band = nir.read(1).astype(float)
            rededge_band = rededge.read(1).astype(float)
            if blue:
                blue_band = blue.read(1).astype(float) if blue_raster_path else None

            # # Compute NDVI
            # start_time_ndvi = time.time()  # Start timing before the loop
            # ndvi = np.where((nir_band + red_band) != 0, (nir_band - red_band) / (nir_band + red_band), np.nan)
            # end_time_ndvi = time.time()  # Stop timing after the loop
            # print(f"⏳ NDVI Compute execution time: {end_time_ndvi - start_time_ndvi:.4f} seconds")
            
            # Compute NDVI (Numba optimized below) This is faster than the one above
            ndvi = compute_ndvi_numba(nir_band, red_band)



            
            """Check if a geometry is valid and intersects raster bounds."""
            # Debugging: print geometry and bounds types
            print(f"Validating geometry ID: {i + 1}")  # Print geometry ID (unique ID for the geometry object)
            
            if geom.is_empty or geom.area == 0:
                return False, "Empty or invalid geometry."
            # Confirming intersection between the shape file element and the raster
            # Convert geometry bounds (tuple) to a shapely box
            geom_box = box(*geom.bounds)
            for band_ in [red, green, nir, rededge]:
                # Convert raster bounds (BoundingBox) to a shapely box
                raster_box = box(*band_.bounds)
                
                if not geom_box.intersects(raster_box):
                    print(f"Geometry {i} does not intersect the raster extent.")
                    continue
    
            # Calculate statistics
            stats_df.loc[shp_crs['id'][i], [f"NDVI_{stat}" for stat in calculate_band_statistics(ndvi, geom, red.transform).keys()]] = \
                list(calculate_band_statistics(ndvi, geom, red.transform).values())

            stats_df.loc[shp_crs['id'][i], [f"red_{stat}" for stat in calculate_band_statistics(red_band, geom, red.transform).keys()]] = \
                list(calculate_band_statistics(red_band, geom, red.transform).values())

            stats_df.loc[shp_crs['id'][i], [f"green_{stat}" for stat in calculate_band_statistics(green_band, geom, green.transform).keys()]] = \
                list(calculate_band_statistics(green_band, geom, green.transform).values())

            stats_df.loc[shp_crs['id'][i], [f"nir_{stat}" for stat in calculate_band_statistics(nir_band, geom, nir.transform).keys()]] = \
                list(calculate_band_statistics(nir_band, geom, nir.transform).values())

            stats_df.loc[shp_crs['id'][i], [f"rededge_{stat}" for stat in calculate_band_statistics(rededge_band, geom, rededge.transform).keys()]] = \
                list(calculate_band_statistics(rededge_band, geom, rededge.transform).values())

            if blue:
                stats_df.loc[shp_crs['id'][i], [f"blue_{stat}" for stat in calculate_band_statistics(blue_band, geom, blue.transform).keys()]] = \
                    list(calculate_band_statistics(blue_band, geom, blue.transform).values())

            # Update the status of the geometry to 'processed'
            processed_ids.append(shp_crs.iloc[i]['id'])

            end_time = time.time()  # Stop timing after the loop
            print(f"⏳ Loop execution time: {end_time - start_time:.4f} seconds")

        highlight_status = 'Processing Complete'
        if plot_geom == "ortho":
            # Highlight the current ortho geometry being processed
            plot_with_highlighted_ortho_geometry(shp_crs, shp_crs.iloc[i]['id'], highlight_status, processed_ids, ortho_path=rgb_raster_thumb_path, project_name=project_name, flight=flight)
        elif plot_geom == "shp":
            plot_with_highlighted_shp_geometry(shp_crs, shp_crs.iloc[i]['id'], highlight_status, processed_ids, highlight_color='red', edgewidth=3, default_color='lightblue')

    gc.collect()  # Force garbage collection



# @precise_timing_decorator
def process_single_geometry(geom, raster_paths, transform):
    start_time = time.time()  # Start timing before the loop
    try:
        """Processes a single geometry and returns statistics."""
        with rasterio.open(raster_paths["red"]) as red, \
             rasterio.open(raster_paths["green"]) as green, \
             rasterio.open(raster_paths["nir"]) as nir, \
             rasterio.open(raster_paths["rededge"]) as rededge:
    
            red_band = red.read(1).astype(float)
            green_band = green.read(1).astype(float)
            nir_band = nir.read(1).astype(float)
            rededge_band = rededge.read(1).astype(float)
    
            # Compute NDVI (Numba optimized below)
            ndvi = compute_ndvi_numba(nir_band, red_band)
    
            # Calculate statistics
            stats = {
                "NDVI": calculate_band_statistics(ndvi, geom, transform),
                "red": calculate_band_statistics(red_band, geom, transform),
                "green": calculate_band_statistics(green_band, geom, transform),
                "nir": calculate_band_statistics(nir_band, geom, transform),
                "rededge": calculate_band_statistics(rededge_band, geom, transform)
            }
        end_time = time.time()  # Stop timing after the loop
        print(f"⏳ process_single_geometry execution time: {end_time - start_time:.4f} seconds")
    
        return stats

    except Exception as e:
        print(f"Error processing geometry ID {geom}: {e}")
        return None  # Return None so that processing continues
    

# @precise_timing_decorator
def process_rasters_parallel(shp, raster_paths, stats_df):
    start_time = time.time()  # Start timing before the loop

    """Parallelized raster processing for efficiency."""
    
    # Use multiprocessing
    # with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        with rasterio.open(raster_paths["red"]) as red:
            futures = {
                executor.submit(process_single_geometry, geom, raster_paths, red.transform): geom_id
                for geom_id, geom in zip(shp['id'], shp.geometry)
            }
    
            for future in concurrent.futures.as_completed(futures):
                geom_id = futures[future]
                try:
                    stats = future.result()
                    for band, band_stats in stats.items():
                        for stat_name, value in band_stats.items():
                            stats_df.at[geom_id, f"{band}_{stat_name}"] = value
                except Exception as e:
                    print(f"Error processing geometry {geom_id}: {e}")

    end_time = time.time()  # Stop timing after the loop
    print(f"⏳ process_rasters_parallel execution time: {end_time - start_time:.4f} seconds")

    gc.collect()  # Clean up memory after processing


def process_rasters_parallel(shp, raster_paths, stats_df):
    start_time = time.time()  # Start timing before the loop
    """Parallelized raster processing for efficiency."""
    # Convert GeoDataFrame geometries to WKT (Well-Known Text) format for pickling
    shp['geometry_wkt'] = shp['geometry'].apply(lambda geom: geom.wkt)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        with rasterio.open(raster_paths["red"]) as red:

            futures = {
                executor.submit(
                    process_single_geometry, wkt_geom, raster_paths, red.transform
                ): geom_id
                for geom_id, wkt_geom in zip(shp['id'], shp['geometry_wkt'])
            }
    
            for future in concurrent.futures.as_completed(futures):
                geom_id = futures[future]
                try:
                    stats = future.result()
                    for band, band_stats in stats.items():
                        for stat_name, value in band_stats.items():
                            stats_df.at[geom_id, f"{band}_{stat_name}"] = value
                except Exception as e:
                    print(f"Failed processing geometry {geom_id}: {e}")
    end_time = time.time()  # Stop timing after the loop
    print(f"⏳ process_rasters_parallel execution time: {end_time - start_time:.4f} seconds")

    gc.collect()  # Clean up memory after processing


### Optimize NDVI Computation Using Numba

@precise_timing_decorator
@njit
def compute_ndvi_numba(nir, red):
    """Fast NDVI computation using Numba."""
    return np.where((nir + red) == 0, np.nan, (nir - red) / (nir + red))



@precise_timing_decorator
def compute_ndvi_gpu(nir, red):
    """NDVI computation using GPU."""
    nir_gpu = cp.array(nir)
    red_gpu = cp.array(red)
    ndvi_gpu = cp.where((nir_gpu + red_gpu) == 0, cp.nan, (nir_gpu - red_gpu) / (nir_gpu + red_gpu))
    return cp.asnumpy(ndvi_gpu)  # Convert back to NumPy for further processing

@precise_timing_decorator
def compute_ndvi_gpu2(nir, red):
    """Calculate NDVI using GPU acceleration."""
    nir_cp = cp.array(nir, dtype=cp.float32)
    red_cp = cp.array(red, dtype=cp.float32)
    
    ndvi = cp.where((nir_cp + red_cp) != 0, (nir_cp - red_cp) / (nir_cp + red_cp), cp.nan)
    
    return cp.asnumpy(ndvi)  # Convert back to NumPy after computation

def get_project_files(src_folder, project_name, flight_type='MS'):
    """
    Retrieves orthomosaic and DSM/DTM file paths, organized by flight folder.

    Parameters:
    - src_folder (str): Root directory where projects are stored.
    - project_name (str): Name of the project folder.
    - flight_type (str): Flight type, either 'MS' or '3D'.

    Returns:
    - ortho_dict (dict): { flight_folder_name: [list of orthomosaic files] }
    - dsm_dtm_dict (dict): { flight_folder_name: [list of DSM/DTM files] }
    """
    
    print(f"Fetching file lists for project: {project_name}, flight type: {flight_type}")

    # Define base path for the flight type
    flight_type_folder = os.path.join(src_folder, project_name, flight_type)

    # Find all subfolders within the flight type folder (each representing a flight)
    flight_folders = [
        f for f in os.listdir(flight_type_folder)
        if os.path.isdir(os.path.join(flight_type_folder, f))
    ]

    # Initialize dictionaries
    ortho_dict = {}
    dsm_dtm_dict = {}

    # Loop through each flight folder
    for flight_folder in flight_folders:
        flight_path = os.path.join(flight_type_folder, flight_folder)
        ortho_folder = os.path.join(flight_path, "2_Orthomosaics")
        dsm_dtm_folder = os.path.join(flight_path, "3_DSM_DTM_Elevation_Models")

        # Collect orthomosaic files
        if os.path.exists(ortho_folder):
            ortho_files = [os.path.join(ortho_folder, f) for f in os.listdir(ortho_folder) if f.endswith(".tif")]
            if ortho_files:
                ortho_dict[flight_folder] = ortho_files
        elif 'MS' in flight_folder:
            print(f"Warning: Orthomosaics folder not found in {flight_folder}")

        # Collect DSM/DTM files
        if os.path.exists(dsm_dtm_folder):
            dsm_dtm_files = [os.path.join(dsm_dtm_folder, f) for f in os.listdir(dsm_dtm_folder) if f.endswith(".tif")]
            if dsm_dtm_files:
                dsm_dtm_dict[flight_folder] = dsm_dtm_files
        elif '3D' in flight_folder:
            print(f"Warning: DSM/DTM folder not found in {flight_folder}")

    return ortho_dict, dsm_dtm_dict


@precise_timing_decorator
def check_data_completeness(ortho_dict, dsm_dtm_dict):
    """
    Checks if all required orthomosaic and DSM/DTM files are present for each flight folder,
    ensuring consistency in flight types (either "MS" or "3D").

    Parameters:
    - ortho_dict (dict): Dictionary {flight_folder: list_of_orthomosaics}.
    - dsm_dtm_dict (dict): Dictionary {flight_folder: list_of_dsm_dtm_files}.

    Returns:
    - completeness_status (dict): Summary of completeness for each flight.
    - missing_files_report (dict): Flights with missing data and missing filenames.
    """

    completeness_status = {}
    missing_files_report = {}

    # Define required file suffixes for MS and 3D projects
    required_files_ms = {
        "_index_green_green.tif",
        "_index_ndvi.tif",
        "_index_nir_nir.tif",
        "_index_red_edge_red_edge.tif",
        "_index_red_red.tif",
        "_transparent_mosaic_group1.tif"
    }
    optional_blue_band = "_index_blue_blue.tif"

    required_files_3d = {
        "_dtm.tif",
        "_dsm.tif"
    }

    # Identify flight types from folder names
    flight_types = {}
    for flight in list(ortho_dict.keys()) + list(dsm_dtm_dict.keys()):
        if "MS" in flight.upper():
            flight_types[flight] = "MS"
        elif "3D" in flight.upper():
            flight_types[flight] = "3D"
        else:
            flight_types[flight] = "UNKNOWN"

    # Count occurrences of each flight type
    type_counts = Counter(flight_types.values())

    # If there are mixed flight types, identify the minority group and warn the user
    if len(type_counts) > 1:
        print("\n⚠️ WARNING: Inconsistent flight types detected!")
        print("Detected flight types:", type_counts)

        # Find the minority group (least frequent flight type)
        minority_type = min(type_counts, key=type_counts.get)
        minority_flights = [flight for flight, f_type in flight_types.items() if f_type == minority_type]

        print(f"🚨 The following flights are of type '{minority_type}', which may be misplaced:")
        print("\n".join(minority_flights))
        print("Please verify if these are in the correct location.\n")

    # Perform completeness checks
    for flight, f_type in flight_types.items():
        if f_type == "MS":
            # Check for missing MS files
            files = ortho_dict.get(flight, [])
            missing_files = [f for f in required_files_ms if not any(f in file for file in files)]

            # Check for blue band consistency
            blue_band_found = any(optional_blue_band in file for file in files)

            if not missing_files:
                completeness_status[flight] = "✅ Complete"
            else:
                completeness_status[flight] = "❌ Incomplete"
                missing_files_report[flight] = missing_files

        elif f_type == "3D":
            # Check for missing 3D files
            files = dsm_dtm_dict.get(flight, [])
            missing_files = [f for f in required_files_3d if not any(f in file for file in files)]

            if not missing_files:
                completeness_status[flight] = "✅ Complete"
            else:
                completeness_status[flight] = "❌ Incomplete"
                missing_files_report[flight] = missing_files

        else:
            print(f"⚠️ Unknown flight type for {flight}. Skipping data check.")

    return completeness_status, missing_files_report

def drop_incomplete_flights(ortho_dict, dsm_dtm_dict, missing, output_csv_folder):
    """
    Drops flights with missing files from the ortho_dict and dsm_dtm_dict.
    
    Args:
        ortho_dict (dict): Dictionary mapping flight names to orthomosaic file paths.
        dsm_dtm_dict (dict): Dictionary mapping flight names to DSM and DTM file paths.
        missing (dict): Dictionary listing missing files for each flight.
    
    Returns:
        ortho_dict (dict): Updated ortho_dict with incomplete flights removed.
        dsm_dtm_dict (dict): Updated dsm_dtm_dict with incomplete flights removed.
    """
    for flight in list(missing.keys()):  # Use list() to avoid modifying dict during iteration
        if flight in ortho_dict:
            del ortho_dict[flight]
        if flight in dsm_dtm_dict:
            del dsm_dtm_dict[flight]

    # write_missing_projects to csv
    csv_log = os.path.join(output_csv_folder, "Incomplete Flights Log.csv")
    write_missing_projects_to_csv(missing, csv_log)

    return ortho_dict, dsm_dtm_dict

def write_missing_projects_to_csv(missing_projects, csv_file):
    """
    Write the missing projects (with missing files) to a CSV file.
    Each missing file will be logged as a separate row along with the project ID and a note.
    """
    # Check if the CSV file already exists
    file_exists = os.path.isfile(csv_file)
    
    # Open the CSV file in append mode
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'missing_file', 'status'])
        
        # Write the header if the file does not exist
        if not file_exists:
            writer.writeheader()

        # Write each missing project and its corresponding missing files to the CSV
        for project_id, missing_files in missing_projects.items():
            for missing_file in missing_files:
                writer.writerow({
                    'id': project_id,
                    'missing_file': missing_file,
                    'status': 'Incomplete'  # You can change this if you want a different status
                })



def extract_common_prefix(file_paths):
    """Finds the common prefix among a list of file names."""
    common_prefix = os.path.commonprefix([os.path.basename(p) for p in file_paths])
    return re.sub(r'[^a-zA-Z0-9_-]', '', common_prefix.replace(" ", "_"))  # Clean any special characters

def list_geojson_files(geojson_file_folder):
    """
    Lists all geojson files in the specified folder and extracts project names from their filenames.

    Parameters:
    - geojson_file_folder (str): Path to the folder containing geojsonfiles.

    Returns:
    - dict: A dictionary mapping project names to their corresponding geojson file paths.
    """
    geojson_file_dict = {}
    geojson_files = glob.glob(os.path.join(geojson_file_folder, "*.geojson"))

    for shp in geojson_files:
        project_name = os.path.basename(shp).split(".geojson")[0]
        geojson_file_dict[project_name] = shp  # Map project name to geojsonfile path

    return geojson_file_dict

def check_memory_usage(threshold=80):
    """
    Checks memory usage and prints a warning if it exceeds the threshold.
    
    Parameters:
    - threshold (int): Memory usage percentage above which a warning is triggered.
    
    Returns:
    - bool: True if memory usage is high, False otherwise.
    """
    mem = psutil.virtual_memory()
    if mem.percent > threshold:
        print(f"⚠️ WARNING: High memory usage detected ({mem.percent}%). Consider freeing memory.")
        return True
    return False

@precise_timing_decorator
def prepare_and_run_raster_processing(project_name, output_root_folder, ortho_dict, geojson_file_folder):
    """
    Matches orthomosaics to the correct geojson file and prepares necessary data before running process_rasters().

    Parameters:
    - project_name (str): Name of the field project
    - output_root_folder (str): Root path to store output CSV files.
    - ortho_dict (dict): Dictionary mapping flight folders to lists of raster file paths.
    - geojson_file_folder (str): Path to the folder containing geojsonfiles.

    Returns:
    - None
    """
    geojson_file_dict = list_geojson_files(geojson_file_folder)

    for flight, paths in ortho_dict.items():
        print(f"\n🚀 Preparing raster processing for flight: {flight}")

        # Find the corresponding geojsonfile
        matched_geojson_file = next(
            (shp for shp_file_name, shp in geojson_file_dict.items() if project_name in shp_file_name), None
        )

        if not matched_geojson_file:
            print(f"⚠️ No matching geojson file found for {flight}. Skipping...")
            continue

        print(f"✅ Matched geojson file: {matched_geojson_file}")

        
        # Define output file name based on the common prefix of input files
        output_csv_name = f"{extract_common_prefix(paths)}statistics.csv"
        output_csv_path = os.path.join(output_root_folder, project_name, output_csv_name)
        
        # Ensure the the output directory exists
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        
        # **Check if CSV file for the flight being processed already exists**
        if os.path.exists(output_csv_path):
            print(f"📌 Output CSV already exists: {output_csv_path}. Skipping processing.")
            continue  # Skip this flight
        
        # **Monitor memory before loading large files**
        check_memory_usage()

        # Load the GeoJSON file
        try:
            shp = gpd.read_file(matched_geojson_file)
            shp.columns = shp.columns.str.lower() # convert all column names in the GeoDataFrame to lowercase
        except Exception as e:
            print(f"❌ Error loading shapefile {matched_geojson_file}: {e}")
            continue

        # Identify raster paths dynamically
        rgb_raster_path = next((tif for tif in paths if "_transparent_mosaic_group1.tif" in tif), None)
        green_raster_path = next((tif for tif in paths if "green_green" in tif), None)
        nir_raster_path = next((tif for tif in paths if "nir_nir" in tif), None)
        red_raster_path = next((tif for tif in paths if "red_red" in tif), None)
        rededge_raster_path = next((tif for tif in paths if "red_edge_red_edge" in tif), None)
        blue_raster_path = next((tif for tif in paths if "blue_blue" in tif), None)  # Optional
               
        # Ensure all required raster files exist
        if not all([red_raster_path, green_raster_path, nir_raster_path, rededge_raster_path]):
            print(f"❌ Missing required raster files for {flight}. Skipping...")
            continue

        # Downscale the RGB raster for preview during processing
        if rgb_raster_path:
            rgb_raster_thumb_path = add_suffix_to_file_name(rgb_raster_path, "_thumb")
            downscale_image(rgb_raster_path, rgb_raster_thumb_path, 0.05)



        raster_paths = {
            "red": next((tif for tif in paths if "red_red" in tif), None),
            "blue": next((tif for tif in paths if "blue_blue" in tif), None),
            "green": next((tif for tif in paths if "green_green" in tif), None),
            "nir": next((tif for tif in paths if "nir_nir" in tif), None),
            "red_edge": next((tif for tif in paths if "red_edge_red_edge" in tif), None)
        }

        
        # **Check memory usage after loading**
        check_memory_usage()
            
        # Example mock geometry and transform for column preparation
        mock_geom = box(0, 0, 3, 2)  # A simple bounding box geometry
        mock_transform = from_origin(0, 3, 1, 1)  # Example affine transform

        # Prepare an empty DataFrame dynamically
        # Dynamically generate column names based on the statistics function
        stats_columns = [
            f"{band}_{stat}" for band in ["NDVI", "green", "nir", "red", "rededge"]
            for stat in calculate_band_statistics(np.array([[1, 2, 3], [4, 5, 6]]), mock_geom, mock_transform).keys()
        ]
        
        # If blue_raster_path exists, add blue statistics columns
        if blue_raster_path:
            stats_columns.extend([
                f"blue_{stat}" for stat in calculate_band_statistics(np.array([[1, 2, 3], [4, 5, 6]]), mock_geom, mock_transform).keys()
            ])

        # Initialize the output DataFrame using the ID column from the GeoJSON
        stats_df = pd.DataFrame(index=shp["id"], columns=stats_columns)

        # # **Run raster processing**
        process_rasters(shp, project_name, flight, green_raster_path, nir_raster_path, red_raster_path, rededge_raster_path, blue_raster_path, rgb_raster_thumb_path, stats_df, plot_geom = "none")
        # process_rasters_parallel(shp, raster_paths, stats_df)
        
        # plot_geom = "ortho"
        # plot_geom = "shp"
        # plot_geom = "none"
        
        # **Clear raster data from memory**
        gc.collect()  # Force garbage collection
        print(f"🧹 Cleared raster data from memory.")

        # **Clear shapefile from memory**
        del shp
        gc.collect()  # Force garbage collection
        print(f"🧹 Cleared shapefile data from memory.")
        
        # Save results
        stats_df.to_csv(output_csv_path, index_label="id")
        print(f"📁 Saved results to {output_csv_path}")
        
        # **Final memory check**
        check_memory_usage()


def process_multiple_projects(project_names, src_folder, flight_type, geojson_file_folder, output_root_folder):
    """
    Processes multiple projects by fetching orthomosaic files, validating data, and running raster analysis.

    Parameters:
    - project_names (list of str): List of project names to process.
    - src_folder (str): Root folder containing project data.
    - flight_type (str): Either 'MS' or '3D' indicating the flight type.
    - geojson_file_folder (str): Path to folder containing GeoJSON shapefiles.
    - output_root_folder (str): Folder where processed CSV files will be saved.

    Returns:
    - None
    """
    for project_name in project_names:
        print(f"\n🚀 Processing Project: {project_name} | Flight Type: {flight_type}")

        # **Step 1: Generate ortho_dict**
        ortho_dict, dsm_dtm_dict = get_project_files(src_folder, project_name, flight_type)



        completeness, missing = check_data_completeness(ortho_dict, dsm_dtm_dict)

        print("\n✅ COMPLETENESS STATUS:")
        for flight, status in completeness.items():
            print(f"{flight}: {status}")
        
        if missing:
            print("\n❌ MISSING FILES REPORT:")
            for flight, files in missing.items():
                print(f"{flight} is missing: {', '.join(files)}")
        
        # Drop incomplete flights
        ortho_dict, dsm_dtm_dict = drop_incomplete_flights(ortho_dict, dsm_dtm_dict, missing, output_root_folder)
        
        # **Step 4: Run raster processing**
        prepare_and_run_raster_processing(project_name, output_root_folder, ortho_dict, geojson_file_folder)

if __name__ == "__main__":
    # Example usage
    field_ids = ['E166', 'PRO_BAR_VOLL', 'OAT_FRONTIERS', 'DIVERSITY_OATS', 'PILOT', 'PRO_BAR_SØRÅS', 'PHENO_CROP']
    src_folder = r"D:\PhenoCrop\2_pix4d_cleaned"
    project_names = [field for field in os.listdir(src_folder) if field in field_ids]   # List of projects
    project_names = ['E166', 'PRO_BAR_VOLL', 'OAT_FRONTIERS', 'PRO_BAR_SØRÅS', 'PHENO_CROP', 'DIVERSITY_OATS']   # List of projects
    geojson_file_folder = r'D:\PhenoCrop\3_qgis\3_Extraction Polygons\3. FINAL MASKS PYTHON'
    output_root_folder = r'D:\PhenoCrop\3_python'

    # for flight_type in ["MS", "3D"]:  # Process both flight types
    for flight_type in ["MS"]:  # Process only MS flight types
        process_multiple_projects(project_names, src_folder, flight_type, geojson_file_folder, output_root_folder)



