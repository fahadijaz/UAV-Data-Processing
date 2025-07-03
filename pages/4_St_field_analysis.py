import sys
import os
# Ensuring the project root is in the correct path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

import streamlit as st
import pandas as pd
from modules.flight_log_preprocessing import preprocessing
from modules.file_system_functions import find_files_in_folder
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import math


df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()

#df_flight_log_merged

flight_log_selection = df_flight_log_merged.copy()

qgis_folder_path = "24PROBARG20_Vollebekk_2024.xlsx"

# Reading the excel files (these are test files)
#df0 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240607 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df1 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240612 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df2 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240620 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df3 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240624 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df4 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240703 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df5 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240708 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df6 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240806 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
#df7 = pd.DataFrame(pd.read_csv("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/20240812 PRO_BAR_VOLL M3M 30m MS 80 85.csv"))
df = pd.read_excel("24PROBARG20_Vollebekk_2024.xlsx")
print(df)

# Returns a list of paths to the qgis result files and a list of their dates
def get_qgis_results(qgis_folder_path, selected_field):
    qgis_results_files = []
    qgis_results_dates = []
    qgis_results_drone = ""
    qgis_results_year = ""
    if selected_field != None:
        selected_field_ID = df_fields.loc[df_fields["LongName"] == selected_field, "Field ID"].values[0]

        qgis_field_folder = rf"{qgis_folder_path}/{selected_field_ID}"

        qgis_results_file_paths = find_files_in_folder(qgis_field_folder, 'csv')
        
        # Only runs the next part if there exists results files
        if qgis_results_file_paths != [""]:
            #qgis_results_dates = [path.split("\\")[1].split(" ")[0][4:] for path in qgis_results_file_paths]
            qgis_results_details = qgis_results_file_paths[0].split("\\")[1].split(" ")
            qgis_results_drone = qgis_results_details[2]
            qgis_results_year = qgis_results_details[0][:4]

            # Makes a list of the dates for the qgis result files in the format dd.mm
            qgis_results_dates = []
            for path in qgis_results_file_paths:
                mm = path.split("\\")[1].split(" ")[0][4:6]
                dd = path.split("\\")[1].split(" ")[0][6:]
                date = rf"{dd}.{mm}"
                qgis_results_dates.append(date)

            # Makes dataframes from the paths
            for path in qgis_results_file_paths:
                qgis_file = pd.DataFrame(pd.read_csv(path))
                qgis_results_files.append(qgis_file)
    
    return qgis_results_files, qgis_results_dates, qgis_results_drone, qgis_results_year

# Returns (a) a list containing the selected indices for the user-selected indices, and (b) a list containing the corresponding indice column names.
def indices_get_selected(input_indices, indices_column_names, input_data_type):
    # Makes a dictionary with the indices as keys and the corresponding column names as values based on the selected data type
    indices_to_selected_data_type = dict(zip(indices_column_names["Indices"], indices_column_names[input_data_type]))
    
    if "All" in input_indices:
        selected_indices = indices_column_names["Indices"]
        selected_indice_column_names = list(indices_to_selected_data_type.values())
    else:
        selected_indices = [indice for indice in input_indices if indice in indices_to_selected_data_type]
        selected_indice_column_names = [indices_to_selected_data_type[indice] for indice in input_indices if indice in indices_to_selected_data_type]
    
    return selected_indices, selected_indice_column_names

# Checks if the indices have corresponding columns in the statistics files
def indices_check_if_exist(indices, indice_column_names, df_stat_file):
    final_indices_column_names = []
    final_indices = []
    for idx, indice_column_name in enumerate(indice_column_names):
        if indice_column_name in df_stat_file.columns:
            final_indices_column_names.append(indice_column_name)
            final_indices.append(indices[idx])
    
    return final_indices, final_indices_column_names

# A dictionary containing the indices' column names in the files for the zonal statistics
indices_column_names = {"Indices": ["Blue", "Green", "NDVI", "NIR", "Red Edge", "Red"],
                        "Mean": ["blue_mean", "green_mean", "ndvi_mean", "nir_mean", "red_edge_mean", "red_mean"],
                        "Median": ["blue_median", "green_median", "ndvi_median", "nir_median", "red_edge_median", "red_median"],
                        "Standard Deviation": ["blue_stdev", "green_stdev", "ndvi_stdev", "nir_stdev", "red_edge_stdev", "red_stdev"]}

# Options for input fields
excluded_field_IDs = ["Proteinbar NAPE", "GENE2BREAD", "High Grass", "Faba Bean"]
field_IDs = [value for value in df_fields["LongName"] if value not in excluded_field_IDs]
route_types = ["3D", "MS", "phantom-MS"]
data_types = ["Mean", "Median", "Standard Deviation"]
indices_options = ["All"] + indices_column_names["Indices"]

# Creating input fields
input_col_1, input_col_2, input_col_3 = st.columns(3)
with input_col_1:
    input_field = st.selectbox("Field", field_IDs, index=None, placeholder="*Field", label_visibility="collapsed")
with input_col_2:
    current_year = datetime.datetime.now().year
    input_year = st.number_input("Year", min_value=1900, max_value=current_year, step=1, value=current_year, placeholder="*Year", label_visibility="collapsed")
with input_col_3:
    input_flight_type = st.selectbox("Flight Type", route_types, index=None, placeholder="Flight Type", label_visibility="collapsed")

input_col_4, input_col_5 = st.columns(2)
with input_col_4:
    input_data_type = st.selectbox("Data Type", data_types, index=None, placeholder="*Data Type", label_visibility="collapsed")
with input_col_5:
    input_indices = st.multiselect("Indices", indices_options, placeholder="*Indices", label_visibility="collapsed")


qgis_results_files, qgis_results_dates, qgis_results_drone, qgis_results_year = get_qgis_results(qgis_folder_path, input_field)



def display_statistics_boxplot():
    # Check if the necessary input fields are non-empty
    ok_display_statistics_boxplot = 1
    error_message = ""
    ok_display_statistics_boxplot, error_message = (0, "Fill the necessary input fields") if input_data_type is None else (ok_display_statistics_boxplot, error_message)
    ok_display_statistics_boxplot, error_message = (0, "Fill the necessary input fields") if input_indices is None else (ok_display_statistics_boxplot, error_message)
    ok_display_statistics_boxplot, error_message = (0, "This field has no statistics yet") if qgis_results_files == [] else (ok_display_statistics_boxplot, error_message)
    ok_display_statistics_boxplot, error_message = (0, "Fill the necessary input fields") if input_field is None else (ok_display_statistics_boxplot, error_message)

    if ok_display_statistics_boxplot == 1:
        selected_indices, selected_indice_column_names = indices_get_selected(input_indices, indices_column_names, input_data_type)
        final_indices, final_indices_column_names = indices_check_if_exist(selected_indices, selected_indice_column_names, qgis_results_files[0])

        #st.write(final_indices)
        #st.write(final_indices_column_names)

        # Creating grid
        def create_grid(length, columns_per_row):
            grid = []
            rows = math.ceil(length/columns_per_row)
            for row in range(rows):
                grid.append(st.columns(columns_per_row))

            return grid
        
        def get_grid_position(pos_nr, columns_per_row):
            row = math.floor(pos_nr/columns_per_row)
            col = pos_nr-(row*columns_per_row)
            return row, col

        # Oppretter et rutenett for plottene
        grid = create_grid(len(final_indices), 2)
        
        # Plotter plottene i rutenettet
        for idx, selected_indice_column_name in enumerate(final_indices_column_names):
            # new dataframe for holding all red mean values
            df_stats = pd.DataFrame()
            for idy, result_date in enumerate(qgis_results_dates):
                result_file = qgis_results_files[idy]
                df_stats[result_date] = result_file[selected_indice_column_name]

            # Set the figure size
            plt.figure(figsize=(8, 5))  # width=8, height=5
            plt.xticks(rotation=45) # Rotates the labels on the x axis

            sns.set(style='whitegrid')
            sns.boxplot(data=df_stats).set(title=f'{input_field} {qgis_results_year}\n{final_indices[idx]} {input_data_type}\n{qgis_results_drone} MS')


            # # ============================================================================================================================ #
            # # AN ALTERNATE PLOT WITH SEABORN
            # # Create a function to customize the axes of all the subsequent graphs in a uniform way.
            # def add_cosmetics(title=f'{input_field} {qgis_results_year}\n{final_indices[idx]} {input_data_type}\n{qgis_results_drone} MS', 
            #                 xlabel='Flights', ylabel='Index value'):
            #     plt.title(title, fontsize=22)
            #     plt.xlabel(xlabel, fontsize=20)
            #     plt.ylabel(ylabel, fontsize=20)
            #     plt.xticks(fontsize=18)
            #     plt.yticks(fontsize=18)
            #     sns.despine()

            # plt.figure(figsize=(15, 10))
            # # Create violin plots without mini-boxplots inside.
            # ax = sns.violinplot(data=df_stats,
            #                     color='mediumslateblue', 
            #                     cut=0, inner=None)
            # # Clip the right half of each violin.
            # for item in ax.collections:
            #     x0, y0, width, height = item.get_paths()[0].get_extents().bounds
            #     item.set_clip_path(plt.Rectangle((x0, y0), width/2, height,
            #                     transform=ax.transData))
            # # Create strip plots with partially transparent points of different colors depending on the group.
            # num_items = len(ax.collections)
            # sns.stripplot( data=df_stats,
            #             palette=['blue', 'deepskyblue'], alpha=0.4, size=7)
            # # Shift each strip plot strictly below the correponding volin.
            # for item in ax.collections[num_items:]:
            #     item.set_offsets(item.get_offsets() + 0.15)
            # # Create narrow boxplots on top of the corresponding violin and strip plots, with thick lines, the mean values, without the outliers.
            # sns.boxplot(data=df_stats, width=0.35,
            #             showfliers=False, showmeans=True, 
            #             meanprops=dict(marker='o', markerfacecolor='darkorange',
            #                         markersize=10, zorder=3),
            #             boxprops=dict(facecolor=(0,0,0,0), 
            #                         linewidth=3, zorder=3),
            #             whiskerprops=dict(linewidth=3),
            #             capprops=dict(linewidth=3),
            #             medianprops=dict(linewidth=3)).set(title=f'{input_field} {qgis_results_year}\n{final_indices[idx]} {input_data_type}\n{qgis_results_drone} MS')
            # plt.legend(frameon=False, fontsize=15, loc='lower left')
            # add_cosmetics(xlabel='Flights', ylabel='Index value')
            # # ============================================================================================================================ #

            # Showing the plot in the correct cell of the grid
            row, col = get_grid_position(idx, 2)
            with grid[row][col]:
                st.pyplot(plt, clear_figure=True)
    else:
        st.write(error_message)

display_statistics_boxplot()
