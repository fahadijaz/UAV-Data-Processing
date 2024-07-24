import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load excel sheet
drone_flying_schedule = pd.read_excel("Drone Flying Schedule.xlsx", sheet_name='Flight Schedule')

# Convert to pandas dataframe

# Group by week, field and route type
