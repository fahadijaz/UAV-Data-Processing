import streamlit as st
import pandas as pd
from modules.flight_log_preprocessing import preprocessing
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import math

df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()

#df_flight_log_merged

flight_log_selection = df_flight_log_merged.copy()


# Reading the excel files (these are test files)
df0 = pd.DataFrame(pd.read_excel("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/phenocrop-2023-M3MS-20m-20230614.xlsx"))
df1 = pd.DataFrame(pd.read_excel("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/phenocrop-2023-M3MS-20m-20230622.xlsx"))
df2 = pd.DataFrame(pd.read_excel("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/phenocrop-2023-M3MS-20m-20230628.xlsx"))
df3 = pd.DataFrame(pd.read_excel("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/phenocrop-2023-M3MS-20m-20230708.xlsx"))
df4 = pd.DataFrame(pd.read_excel("P:/PhenoCrop/Test_Folder/Test_SINDRE/Phenocrop_M3MS_boxplot/data/phenocrop-2023-M3MS-20m-20230714.xlsx"))

dates = ['20230614', '20230622', '20230628', '20230708', '20230714']


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

indices_check_if_exist(indices_column_names["Indices"], indices_column_names, df0)

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



def display_statistics_boxplot():
    # Check if the necessary input fields are non-empty
    ok_display_statistics_boxplot = 1
    ok_display_statistics_boxplot = 0 if input_field is None else ok_display_statistics_boxplot
    ok_display_statistics_boxplot = 0 if input_data_type is None else ok_display_statistics_boxplot
    ok_display_statistics_boxplot = 0 if input_indices == [] else ok_display_statistics_boxplot

    if ok_display_statistics_boxplot == 1:

        selected_indices, selected_indice_column_names = indices_get_selected(input_indices, indices_column_names, input_data_type)
        final_indices, final_indices_column_names = indices_check_if_exist(selected_indices, selected_indice_column_names, df0)

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
            df_stats[dates[0]]=df0[selected_indice_column_name]
            df_stats[dates[1]]=df1[selected_indice_column_name]
            df_stats[dates[2]]=df2[selected_indice_column_name]
            df_stats[dates[3]]=df3[selected_indice_column_name]
            df_stats[dates[4]]=df4[selected_indice_column_name]

            # Set the figure size
            plt.figure(figsize=(8, 5))  # width=8, height=5

            sns.set(style='whitegrid')
            sns.boxplot(data=df_stats).set(title=f'Phenocrop M3MS {input_data_type} {final_indices[idx]}')
            
            # Showing the plot in the correct cell of the grid
            row, col = get_grid_position(idx, 2)
            with grid[row][col]:
                st.pyplot(plt, clear_figure=True)
    else:
        st.write("Fill the input fields")

display_statistics_boxplot()
