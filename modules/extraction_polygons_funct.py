from file_system_functions import find_files_in_folder
import os
import math
import geopandas as gpd
from pyproj import Transformer, CRS
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, shape, MultiPolygon, MultiPoint


def polygons_to_centroids(input_geojson, output_geojson):
    """
    Convert a GeoJSON file of polygons to a GeoJSON file of centroid points.
    
    Parameters:
        input_geojson (str): Path to the input GeoJSON file containing polygons.
        output_geojson (str): Path to the output GeoJSON file containing centroid points.
    
    Returns:
        None
    """
    # Load the GeoJSON file as a GeoDataFrame
    gdf = gpd.read_file(input_geojson)
    
    # Calculate centroids for each polygon
    gdf['geometry'] = gdf['geometry'].centroid
    
    # Ensure geometries are now Point objects
    if not all(isinstance(geom, Point) for geom in gdf['geometry']):
        raise ValueError("Not all geometries are centroids (points).")
    
    # Save the GeoDataFrame with centroids as a new GeoJSON file
    gdf.to_file(output_geojson, driver='GeoJSON')



# Reorder the centroids
def reorder_points_by_columns(input_geojson, output_geojson, rotation_angle=0):
    """
    Reorder points in a GeoJSON file such that points are ordered column-first.
    The rotation is used only for ordering purposes; the final output retains original coordinates.
    
    Parameters:
        input_geojson (str): Path to the input GeoJSON file containing points.
        output_geojson (str): Path to the output GeoJSON file with reordered points.
        rotation_angle (float): Angle in degrees to rotate the grid for ordering (default: 0).
    
    Returns:
        None
    """
    # Load GeoJSON file into a GeoDataFrame
    gdf = gpd.read_file(input_geojson)
    
    # Compute the centroid of the whole grid
    grid_centroid = MultiPoint(gdf.geometry).centroid
    
    # Rotate the points temporarily for ordering
    if rotation_angle != 0:
        gdf['rotated_geometry'] = gdf['geometry'].apply(
            lambda geom: rotate(geom, rotation_angle, origin=grid_centroid, use_radians=False)
        )
    else:
        gdf['rotated_geometry'] = gdf['geometry']
    
    # Extract coordinates from rotated geometries for sorting
    gdf['x'] = gdf['rotated_geometry'].apply(lambda geom: geom.x)
    gdf['y'] = gdf['rotated_geometry'].apply(lambda geom: geom.y)
    
    # Sort by x (columns) first, and then by y (rows) within each column
    gdf_sorted = gdf.sort_values(by=['x', 'y'], ascending=[True, False]).reset_index(drop=True)

    # Drop geometry column for exporting the rotated geometry
    gdf_rotated_geometry_sorted = gdf_sorted.drop(columns=['geometry', 'x', 'y'])
    gdf_rotated_geometry_sorted.rename(columns={"rotated_geometry": "geometry"}, inplace=True)

    # Save the rotated GeoDataFrame as a new GeoJSON file
    gdf_rotated_geometry_sorted.to_file(modify_filename(output_geojson, suffix = "_rotated_geometry"), driver="GeoJSON")
    
    # Drop temporary columns for sorting
    gdf_sorted = gdf_sorted.drop(columns=['rotated_geometry', 'x', 'y'])
    
    # Save the reordered GeoDataFrame as a new GeoJSON file
    gdf_sorted.to_file(output_geojson, driver="GeoJSON")

def update_ids(input_geojson, output_centroids_with_IDs, id_start=100, id_end=111, step=100):
    """
    Update the IDs of entries in a GeoDataFrame following a specific sequence.

    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame.
        id_start (int): Starting value for each sequence.
        id_end (int): Ending value (inclusive) for each sequence.
        step (int): Step to increase the starting value after each sequence.

    Returns:
        GeoDataFrame: Updated GeoDataFrame with modified IDs.
    """

    gdf = gpd.read_file(input_geojson)
    


    id_list = []
    current_start = id_start

    while len(id_list) < len(gdf):
        id_list.extend(range(current_start, current_start + (id_end - id_start) + 1))
        current_start += step

    # Ensure the ID list matches the length of the GeoDataFrame
    id_list = id_list[:len(gdf)]
    gdf['ID'] = id_list

    gdf.to_file(output_centroids_with_IDs, driver="GeoJSON")  # Save updated GeoDataFrame


# In case the coordinates of a certain sowing geojson are not in longlat; use this funciton to convert them to longlat

def convert_utm_to_longlat(input_geojson, output_geojson, utm_zone):
    """
    Convert a GeoJSON file with UTM coordinates to Latitude/Longitude (WGS84).
    
    Parameters:
        input_geojson (str): Path to the input GeoJSON file with UTM coordinates.
        output_geojson (str): Path to the output GeoJSON file with WGS84 coordinates.
        utm_zone (int): UTM zone number for the input coordinates (positive for north, negative for south).
        
    Returns:
        None
    """
    # Load the GeoJSON file as a GeoDataFrame
    gdf = gpd.read_file(input_geojson)
    
    # Define the source CRS as the UTM zone (EPSG code)
    if utm_zone > 0:
        source_crs = CRS.from_epsg(32600 + utm_zone)  # Northern hemisphere
    else:
        source_crs = CRS.from_epsg(32700 - utm_zone)  # Southern hemisphere
    
    # Set the GeoDataFrame's CRS
    gdf = gdf.set_crs(source_crs)
    
    # Convert to WGS84 (longitude/latitude)
    gdf = gdf.to_crs("EPSG:4326")
    
    # Save the converted GeoDataFrame to a new GeoJSON file
    gdf.to_file(output_geojson, driver="GeoJSON")


def create_rotated_rectangle(center, width, height, angle, crs="EPSG:4326"):
    """
    Create a rotated rectangle as a polygon in geographic coordinates around the given center point.
    
    Parameters:
        center (tuple): The (longitude, latitude) coordinates of the centroid.
        width (float): The width of the rectangle (in meters or appropriate planar units).
        height (float): The height of the rectangle (in meters or appropriate planar units).
        angle (float): The rotation angle in degrees (counterclockwise).
        crs (str): Coordinate reference system for geographic coordinates (default: EPSG:4326).
    
    Returns:
        dict: GeoJSON-like structure containing the rectangle coordinates in longitude and latitude.
    """
    # Define a planar CRS (e.g., UTM zone based on the center point)
    transformer_to_planar = Transformer.from_crs(crs, CRS("EPSG:3857"), always_xy=True)
    transformer_to_geo = Transformer.from_crs(CRS("EPSG:3857"), crs, always_xy=True)

    # Transform the center to planar coordinates
    center_planar = transformer_to_planar.transform(center[0], center[1])
    
    # Create rectangle corners centered at (0, 0) in the planar space
    rectangle = Polygon([
        (-width / 2, -height / 2),
        (width / 2, -height / 2),
        (width / 2, height / 2),
        (-width / 2, height / 2),
        (-width / 2, -height / 2)
    ])
    
    # Rotate the rectangle
    rotated_rectangle = rotate(rectangle, angle, origin=(0, 0), use_radians=False)
    
    # Translate the rectangle to the given center in planar coordinates
    translated_rectangle = translate(rotated_rectangle, xoff=center_planar[0], yoff=center_planar[1])
    
    # Convert planar coordinates back to geographic coordinates
    geographic_coords = [
        transformer_to_geo.transform(x, y) for x, y in translated_rectangle.exterior.coords
    ]
    
    # Return as GeoJSON-like dictionary
    return {
        "type": "Polygon",
        "coordinates": [geographic_coords]
    }

# Convert the 'geometry' column to MULTIPOLYGON
def convert_to_multipolygon(geojson_dict):
    # Convert GeoJSON-like dict to Shapely geometry
    polygon = shape(geojson_dict)
    
    # Ensure the geometry is a MULTIPOLYGON
    if polygon.geom_type == "Polygon":
        return MultiPolygon([polygon])
    return polygon

def generate_shrinked_polygons(
    input_centroids_with_IDs,
    output_extraction_polygons,
    width,
    height,
    rotation,
    crs="EPSG:4326",
):
    """
    Generate shrinked polygons around centroids, save them to a GeoJSON file, and apply transformations.

    Parameters:
        input_centroids_with_IDs (str): Path to the input GeoJSON file with centroids and IDs.
        output_extraction_polygons (str): Path to the output GeoJSON file for the polygons.
        width (float): Width of the polygons to generate.
        height (float): Height of the polygons to generate.
        rotation (float): Rotation angle of the polygons in degrees.
        crs (str): Coordinate Reference System for the GeoDataFrame (default: "EPSG:4326").

    Returns:
        None
    """
    #FIELD SPECIFIC CODE 2024. Not generalised
    # Correct the coordinates system for E166
    if "e166" in input_centroids_with_IDs.lower():
        convert_utm_to_longlat(input_centroids_with_IDs, input_centroids_with_IDs, 32)

    # Load the GeoJSON file with centroids and IDs
    gdf = gpd.read_file(input_centroids_with_IDs)

    # Create shrinked polygons based on the centroids
    gdf['polygons'] = gdf.geometry.apply(
        lambda point: create_rotated_rectangle(
            (point.x, point.y), width, height, rotation
        )
    )
    
    # Replace the geometry column with the generated polygons
    gdf.drop(columns=["geometry"], inplace=True)
    gdf.rename(columns={"polygons": "geometry"}, inplace=True)
    
    # Convert the polygons to MultiPolygon format
    gdf['geometry'] = gdf['geometry'].apply(convert_to_multipolygon)
    
    # Ensure the GeoDataFrame has a valid CRS
    gdf.set_crs(crs, inplace=True)
    
    # Save the resulting GeoDataFrame as a GeoJSON file
    gdf.to_file(output_extraction_polygons, driver='GeoJSON')

    print(f"Shrinked polygons saved to {output_extraction_polygons}")


def modify_filename(filepath, prefix=None, suffix=None, subfolder=None):
    """
    Modify a file path by adding a prefix, suffix, and optionally creating a new subfolder.

    Parameters:
        filepath (str): The original file path.
        prefix (str, optional): Text to add before the file name. Defaults to None.
        suffix (str, optional): Text to add before the file extension. Defaults to None.
        subfolder (str, optional): Name of a subfolder to include in the path. If provided, the subfolder will be created if it doesn't exist.

    Returns:
        str: The modified file path.
    """
    # Split the file path into directory, filename, and extension
    dir_path, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    
    # Add the subfolder if provided
    if subfolder:
        dir_path = os.path.join(dir_path, subfolder)
        os.makedirs(dir_path, exist_ok=True)  # Create the subfolder if it doesn't exist
    
    # Add prefix and suffix
    if prefix:
        name = prefix + name
    if suffix:
        name = name + suffix

    # Return the modified file path
    return os.path.join(dir_path, name + ext)


def create_metadata_based_on_filename(filenames, conditions, metadata_keys):
    """
    Create a metadata dictionary for each filename based on the matching conditions.

    Parameters:
        filenames (list): List of filenames to process.
        conditions (dict): Dictionary where keys are substrings to match in filenames,
                           and values are tuples containing metadata values.
        metadata_keys (list): List of keys that define the metadata variables to extract.

    Returns:
        dict: Dictionary where each filename is mapped to its metadata dictionary.
    """
    metadata = {}

    # Iterate over each filename
    for filename in filenames:
        filename_lower = filename.lower()
        metadata_dict = {}

        # Check each condition to see if it matches the filename
        for key, condition in conditions.items():
            if key.lower() in filename_lower:
                # Map the tuple values to the metadata keys
                metadata_dict = dict(zip(metadata_keys, condition))

        # Add the metadata dictionary for the current filename
        metadata[filename] = metadata_dict

    return metadata


