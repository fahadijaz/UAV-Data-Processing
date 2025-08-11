import pandas as pd
import os


downloads_path = os.path.expanduser("~/Downloads")
csv_file_path = os.path.join(downloads_path, "24BPROBARG20_Vollebekk_2024.csv")

df = pd.read_csv(csv_file_path)

duplicates = df[df.duplicated(subset=["date"])]
print(duplicates)
unique_dates = (
    pd.to_datetime(df["date"], errors="coerce")
    .dt.strftime("%Y-%m-%d")
    .drop_duplicates()
    .sort_values()
    .tolist()
)

print(unique_dates)