import pandas as pd
import streamlit as st
from mitosheet.streamlit.v1 import spreadsheet

st.set_page_config(layout="wide")
#st.title('Drone Flying Schedule')

st.markdown(
    """
        <style>
            .appview-container .main .block-container {{
                padding-top: {padding_top}rem;
                padding-right: {padding_right}rem;
                padding-left: {padding_left}rem;
                }}

        </style>""".format(
        padding_top=0.2, padding_right=0, padding_left=0
    ),
    unsafe_allow_html=True,
)

#drone_flying_schedule = pd.read_excel("Drone Flying Schedule.xlsx", sheet_name='Flight Log')
drone_flying_schedule = pd.read_csv("Flight Log.csv")

final_dfs, code = spreadsheet(drone_flying_schedule, height="1250px")

#st.write(final_dfs)
#st.code(code)
