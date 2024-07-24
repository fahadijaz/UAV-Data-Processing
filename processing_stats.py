import pandas as pd
import streamlit as st

flight_log = pd.read_csv("Flight Log.csv")

flight_log = flight_log[flight_log["ID"] == "PHENO"]
flight_log = flight_log[flight_log["Route type"] == "MS"]
flight_log = flight_log[flight_log["Drone Pilot"] == "Isak"]
st.dataframe(flight_log)