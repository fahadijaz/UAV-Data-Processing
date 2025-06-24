import sqlite3
import pandas as pd

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DB_PATH = "drone_data.db"

PILOTS_EXCEL_PATH = r"database_source.xlsx"
PILOTS_SHEET_NAME = "Pilots"

DRONES_EXCEL_PATH = r"database_source.xlsx"
DRONES_SHEET_NAME = "Drones"

# ==============================================================================
# DATA READING FUNCTIONS
# ==============================================================================

def read_pilots_from_excel(file_path: str, sheet_name: str) -> list:
    """
    Load unique pilot names from a specified Excel sheet.

    Args:
        file_path (str): Path to the Excel workbook.
        sheet_name (str): Sheet name containing pilot data with a 'name' column.

    Returns:
        list[str]: List of unique pilot names.

    Raises:
        ValueError: If the required 'name' column is missing.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    if 'name' not in df.columns:
        raise ValueError("Expected a column named 'name' in the pilots sheet.")
    return df['name'].dropna().drop_duplicates().astype(str).tolist()


def read_drones_from_excel(file_path: str, sheet_name: str) -> list:
    """
    Load unique drone model names from a specified Excel sheet.

    Args:
        file_path (str): Path to the Excel workbook.
        sheet_name (str): Sheet name containing drone data with a 'model' column.

    Returns:
        list[str]: List of unique drone models.

    Raises:
        ValueError: If the required 'model' column is missing.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    if 'model' not in df.columns:
        raise ValueError("Expected a column named 'model' in the drones sheet.")
    return df['model'].dropna().drop_duplicates().astype(str).tolist()

# ==============================================================================
# DATABASE SCHEMA SETUP
# ==============================================================================

def initialize_drone_database(db_path: str = DB_PATH) -> None:
    """
    Creates or initializes required tables in the SQLite database.

    Tables:
        - pilots:        (name TEXT PRIMARY KEY)
        - drones:        (model TEXT PRIMARY KEY)
        - flight_routes: Stores predefined flight routes.
        - flight_log:    Stores flight activity logs.

    Args:
        db_path (str): Path to the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS pilots (
        name TEXT PRIMARY KEY
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS drones (
        model TEXT PRIMARY KEY
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS flight_routes (
        FlightRoute TEXT PRIMARY KEY,
        BasePath TEXT,
        FieldName TEXT,
        Drone TEXT,
        Equipment_ID TEXT,
        FlightHeight INTEGER,
        BaseType TEXT,
        SideOverlap REAL,
        FrontOverlap REAL,
        CameraAngle INTEGER,
        FlightSpeed REAL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS flight_log (
        flight_ID TEXT PRIMARY KEY,
        dir_name TEXT,
        flight_name TEXT,
        date TEXT,
        folder_ID TEXT,
        start_time TEXT,
        end_time TEXT,
        type TEXT,
        num_files INTEGER,
        num_dir INTEGER,
        output_path TEXT,
        height INTEGER,
        drone_pilot TEXT,
        drone TEXT
        -- Additional columns can be added later
    )""")

    conn.commit()
    conn.close()

# ==============================================================================
# DATABASE INSERTION
# ==============================================================================

def insert_into_db(pilots: list, drones: list) -> None:
    """
    Inserts pilot names and drone models into their respective database tables.

    Args:
        pilots (list[str]): List of pilot names.
        drones (list[str]): List of drone model names.

    Notes:
        - Uses INSERT OR IGNORE to avoid duplicate entries.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executemany("INSERT OR IGNORE INTO pilots (name) VALUES (?)", [(p,) for p in pilots])
    cur.executemany("INSERT OR IGNORE INTO drones (model) VALUES (?)", [(d,) for d in drones])

    conn.commit()
    conn.close()
    print("Pilots and drones inserted.")

# ==============================================================================
# ROUTE INFO RETRIEVAL - FULL PROJECT MAPPING
# ==============================================================================

def get_flight_route_info() -> dict:
    """
    Retrieves all flight route and flight log information organized by project (BasePath).

    Returns:
        dict[str, dict]: A dictionary structured as:
            {
                "project_name_or_basepath": {
                    "output_path": str,
                    "flight_routes": list[dict],
                    "flight_log": list[dict]
                },
                ...
            }

    Notes:
        - Uses `BasePath` as the primary key to group related routes and logs.
        - If no matching logs exist for a project, the `flight_log` list will be empty.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like row access
    cur = conn.cursor()

    # Fetch all routes
    cur.execute("SELECT * FROM flight_router")
    route_rows = cur.fetchall()

    # Organize routes by BasePath
    project_data = {}
    for row in route_rows:
        route = dict(row)
        project = route.get("BasePath")

        if project not in project_data:
            project_data[project] = {
                "output_path": project,
                "flight_routes": [],
                "flight_log": []
            }
        project_data[project]["flight_routes"].append(route)

    # Fetch all logs
    cur.execute("SELECT * FROM flight_log")
    log_rows = cur.fetchall()

    for log in log_rows:
        log_entry = dict(log)
        log_path = log_entry.get("output_path")
        if log_path in project_data:
            project_data[log_path]["flight_log"].append(log_entry)

    conn.close()
    return project_data


# ==============================================================================
# FLIGHT LOGGING
# ==============================================================================

def log_flight_entry(entry: dict) -> None:
    """
    Inserts or updates a flight log record in the `flight_log` table.

    Args:
        entry (dict): Dictionary where keys match column names in `flight_log`.

    Behavior:
        - Replaces any existing entry with the same `flight_ID`.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    placeholders = ', '.join(['?'] * len(entry))
    columns = ', '.join(entry.keys())
    sql = f"""
        INSERT OR REPLACE INTO flight_log ({columns})
        VALUES ({placeholders})
    """
    cur.execute(sql, list(entry.values()))

    conn.commit()
    conn.close()

# ==============================================================================
# MAIN SCRIPT ENTRY
# ==============================================================================

def main() -> None:
    """
    Loads pilot and drone data from Excel and populates the database.
    Intended for one-time or batch setup.
    """
    pilots = read_pilots_from_excel(PILOTS_EXCEL_PATH, PILOTS_SHEET_NAME)
    drones = read_drones_from_excel(DRONES_EXCEL_PATH, DRONES_SHEET_NAME)

    initialize_drone_database()
    insert_into_db(pilots, drones)

if __name__ == "__main__":
    main()
