import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from rasterio.features import geometry_mask

# Load the shapefile
shp = gpd.read_file("P:/PhenoCrop/3_qgis/shape files new/Phenocrop.geojson")

# Paths to individual band rasters
red_raster_path = "P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/20240624 PHENO P4M 20m MS_index_red_red.tif"
blue_raster_path = "P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/20240624 PHENO P4M 20m MS_index_blue_blue.tif"
green_raster_path = "P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/20240624 PHENO P4M 20m MS_index_green_green.tif"
nir_raster_path = "P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/20240624 PHENO P4M 20m MS_index_nir_nir.tif"
redE_raster_path = "P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/20240624 PHENO P4M 20m MS_index_red_edge_red_edge.tif"

# Try to load an existing DataFrame, or start a new one
try:
    stats_df = pd.read_csv('P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/combined_band_statistics.csv')
    # Find the last complete row
    last_complete_row = stats_df.dropna().index[-1] + 1
    print(f"Resuming from row {last_complete_row}")
except (FileNotFoundError, IndexError):  # Handle cases where no file exists or no complete rows
    print("Starting from scratch")
    last_complete_row = 0
    columns = ['NDVI_med', 'NDVI_mean', 'NDVI_std',
               'red_med', 'red_mean', 'red_std',
               'blue_med', 'blue_mean', 'blue_std',
               'green_med', 'green_mean', 'green_std',
               'nir_med', 'nir_mean', 'nir_std',
               'redE_med', 'redE_mean', 'redE_std']
    stats_df = pd.DataFrame(index=range(len(shp)), columns=columns)

def calculate_band_statistics(band_array, geom, transform):
    mask = geometry_mask([geom], transform=transform, invert=True, out_shape=band_array.shape)
    masked_values = band_array[mask]
    return np.nanmedian(masked_values), np.nanmean(masked_values), np.nanstd(masked_values)

def process_rasters(start_index):
    with rasterio.open(red_raster_path) as red, \
         rasterio.open(blue_raster_path) as blue, \
         rasterio.open(green_raster_path) as green, \
         rasterio.open(nir_raster_path) as nir, \
         rasterio.open(redE_raster_path) as redE:
        for i, geom in enumerate(shp.geometry[start_index:], start=start_index):
            print(f"Processing geometry {i}")
            # Calculate NDVI and other statistics
            red_band = red.read(1).astype(float)
            nir_band = nir.read(1).astype(float)
            ndvi = (nir_band - red_band) / (nir_band + red_band + 0.0001)

            # Statistics calculation
            stats_df.loc[i, 'NDVI_med'], stats_df.loc[i, 'NDVI_mean'], stats_df.loc[i, 'NDVI_std'] = calculate_band_statistics(ndvi, geom, red.transform)
            # Repeat for other bands

            # Save intermediate results
            if (i % 100 == 0 or i == len(shp) - 1):
                stats_df.to_csv('P:/PhenoCrop/Phenotyping 2024/PHENO/MS/20240624 PHENO P4M 20m MS/band_data/combined_band_statistics.csv', index=False)
                print(f"Saved progress at row {i}")

if __name__ == "__main__":

    # Start processing from the last complete row or from scratch if necessary
    process_rasters(last_complete_row)
