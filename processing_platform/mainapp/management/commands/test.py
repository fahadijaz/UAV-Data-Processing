import pandas as pd

file_path = r"/Users/ivareftedal/Library/Application Support/Microsoft/Drone_Flying_Schedule_2025.xlsx"

df = pd.read_excel(file_path, sheet_name="Flight Log")
print(df.columns.tolist())
