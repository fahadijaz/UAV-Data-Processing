import sqlite3
import pandas as pd

# ==========================
# Configuration
# ==========================

# Path to Excel file containing pilot data
PILOTS_EXCEL_PATH = r"database\database_source.xlsx"
# Name of the sheet in the pilot Excel file
PILOTS_SHEET_NAME = "Pilots"

# Path to Excel file containing drone model data
DRONES_EXCEL_PATH = r"database\database_source.xlsx"
# Name of the sheet in the drone Excel file
DRONES_SHEET_NAME = "Drones"

# ==========================
# Data Reading Functions
# ==========================

def read_pilots_from_excel(file_path: str, sheet_name: str) -> list:
    """
    Reads pilot names from a specified Excel sheet.

    Args:
        file_path (str): Path to the Excel file.
        sheet_name (str): Name of the sheet containing pilot names.

    Returns:
        list: A list of unique pilot names (strings).
    
    Raises:
        ValueError: If the expected 'name' column is not found in the sheet.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    if 'name' not in df.columns:
        raise ValueError("Expected a column named 'name' in the pilots sheet.")

    # Clean and return unique names
    return df['name'].dropna().drop_duplicates().astype(str).tolist()


def read_drones_from_excel(file_path: str, sheet_name: str) -> list:
    """
    Reads drone model names from a specified Excel sheet.

    Args:
        file_path (str): Path to the Excel file.
        sheet_name (str): Name of the sheet containing drone models.

    Returns:
        list: A list of unique drone models (strings).

    Raises:
        ValueError: If the expected 'model' column is not found in the sheet.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    if 'model' not in df.columns:
        raise ValueError("Expected a column named 'model' in the drones sheet.")

    # Clean and return unique models
    return df['model'].dropna().drop_duplicates().astype(str).tolist()

# ==========================
# Database Population
# ==========================

def insert_into_db(pilots: list, drones: list):
    """
    Inserts pilot names and drone models into a SQLite database.

    Args:
        pilots (list): List of pilot names to insert.
        drones (list): List of drone models to insert.

    Behavior:
        - Creates tables `pilots` and `drones` if they don't exist.
        - Avoids inserting duplicate records by using `INSERT OR IGNORE`.
    """
    # Connect to SQLite database (will create file if it doesn't exist)
    conn = sqlite3.connect("drone_data.db")
    cur = conn.cursor()

    # Create tables with UNIQUE constraint to prevent duplicates
    cur.execute("CREATE TABLE IF NOT EXISTS pilots (name TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS drones (model TEXT UNIQUE)")

    # Insert data using parameterized queries
    cur.executemany("INSERT OR IGNORE INTO pilots (name) VALUES (?)", [(p,) for p in pilots])
    cur.executemany("INSERT OR IGNORE INTO drones (model) VALUES (?)", [(d,) for d in drones])

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database updated successfully.")

# ==========================
# Main Script Entry
# ==========================

def main():
    """
    Main function that reads pilot and drone data from Excel files
    and populates the local SQLite database.
    """
    # Read data from Excel files
    pilots = read_pilots_from_excel(PILOTS_EXCEL_PATH, PILOTS_SHEET_NAME)
    drones = read_drones_from_excel(DRONES_EXCEL_PATH, DRONES_SHEET_NAME)

    # Insert the data into the SQLite database
    insert_into_db(pilots, drones)

# Run the script
if __name__ == "__main__":
    main()
