import streamlit as st
import pandas as pd
from modules.flight_log_preprocessing import preprocessing
import datetime

df_flight_log, df_flight_routes, df_fields, df_flight_log_merged, df_processing_status = preprocessing()

#df_flight_log_merged

flight_log_selection = df_flight_log_merged.copy()

# Options for input fields
excluded_field_IDs = ["Proteinbar NAPE", "GENE2BREAD", "High Grass", "Faba Bean"]
field_IDs = [value for value in df_fields["LongName"] if value not in excluded_field_IDs]
route_types = ("3D", "MS", "phantom-MS")
data_types = ("Mean", "Median", "Std")
indices_options = ("All", "Blue", "Green", "NDVI", "NIR", "Red Edge", "Red")

# Creating input fields
input_col_1, input_col_2, input_col_3 = st.columns(3)
with input_col_1:
    input_field = st.selectbox("Field", field_IDs, index=None, placeholder="Field", label_visibility="collapsed")
with input_col_2:
    current_year = datetime.datetime.now().year
    input_year = st.number_input("Year", min_value=1900, max_value=current_year, step=1, value=current_year, placeholder="Year", label_visibility="collapsed")
with input_col_3:
    input_flight_type = st.selectbox("Flight Type", route_types, index=None, placeholder="Flight Type", label_visibility="collapsed")

input_col_4, input_col_5 = st.columns(2)
with input_col_4:
    input_data_type = st.selectbox("Data Type", data_types, index=None, placeholder="Data Type", label_visibility="collapsed")
with input_col_5:
    input_indices = st.multiselect("Indices", indices_options, placeholder="Indices", label_visibility="collapsed")
