import streamlit as st
import sqlite3
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DB_PATH = "database/drone_data.db"

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

@st.cache_data
def get_options_from_db():
    """
    Retrieves the list of available pilots and drones from the database.

    Returns:
        tuple: (list of pilots, list of drones)
    """
    with sqlite3.connect(DB_PATH) as conn:
        pilots = [row[0] for row in conn.execute("SELECT name FROM pilots")]
        drones = [row[0] for row in conn.execute("SELECT model FROM drones")]
    return pilots, drones

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
# ROUTE ENTRY FORM
# ==============================================================================

def add_flight_route_form():
    """
    Displays a form for adding a new flight route to the `flight_routes` table.

    Fields:
        - FlightRoute (unique ID)
        - BasePath
        - FieldName
        - Drone (dropdown)
        - Equipment_ID
        - FlightHeight
        - BaseType
        - SideOverlap
        - FrontOverlap
        - CameraAngle
        - FlightSpeed

    Behavior:
        - Inserts a new flight route or displays an error if the ID exists.
    """
    st.subheader("➕ Add New Flight Route")

    with st.form("add_route_form"):
        FlightRoute = st.text_input("Route ID (unique)", placeholder="Route_001")
        BasePath = st.text_input("Base Path / Project Folder")
        FieldName = st.text_input("Field Name")
        Drone = st.selectbox("Drone", drones)
        Equipment_ID = st.text_input("Equipment ID")
        FlightHeight = st.number_input("Flight Height (m)", min_value=0)
        BaseType = st.selectbox("Base Type", ["GNSS", "Visual", "Mixed"])
        SideOverlap = st.number_input("Side Overlap (%)", min_value=0.0, max_value=100.0)
        FrontOverlap = st.number_input("Front Overlap (%)", min_value=0.0, max_value=100.0)
        CameraAngle = st.slider("Camera Angle (°)", 0, 90, 90)
        FlightSpeed = st.number_input("Flight Speed (m/s)", min_value=0.0)

        submitted = st.form_submit_button("Add Route")
        if submitted:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO flight_routes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        FlightRoute, BasePath, FieldName, Drone, Equipment_ID,
                        FlightHeight, BaseType, SideOverlap, FrontOverlap,
                        CameraAngle, FlightSpeed
                    ))
                    conn.commit()
                    st.success(f"✅ Flight route '{FlightRoute}' added.")
                except sqlite3.IntegrityError:
                    st.error("❌ A route with this ID already exists.")


# ==============================================================================
# FLIGHT LOG ENTRY FORM
# ==============================================================================

def add_flight_log_form():
    """
    Displays a form for logging a new flight into the `flight_log` table.

    Fields:
        - flight_ID (unique)
        - dir_name
        - flight_name
        - date
        - folder_ID
        - start_time, end_time
        - type
        - num_files, num_dir
        - output_path
        - height
        - drone_pilot (dropdown)
        - drone (dropdown)

    Behavior:
        - Inserts a new log or returns error if flight_ID already exists.
    """
    st.subheader("🛬 Add New Flight Log")

    with st.form("add_log_form"):
        flight_ID = st.text_input("Flight ID (unique)", placeholder="Log_001")
        dir_name = st.text_input("Directory Name")
        flight_name = st.text_input("Flight Name")
        date = st.date_input("Date", value=datetime.today())
        folder_ID = st.text_input("Folder ID")
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        type_ = st.selectbox("Flight Type", ["Survey", "Test", "Mapping", "Other"])
        num_files = st.number_input("Number of Files", min_value=0)
        num_dir = st.number_input("Number of Directories", min_value=0)
        output_path = st.text_input("Output Path (should match project BasePath)")
        height = st.number_input("Flight Height (m)", min_value=0)
        drone_pilot = st.selectbox("Pilot", pilots)
        drone = st.selectbox("Drone", drones)

        submitted = st.form_submit_button("Add Flight Log")
        if submitted:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO flight_log (
                            flight_ID, dir_name, flight_name, date,
                            folder_ID, start_time, end_time, type,
                            num_files, num_dir, output_path, height,
                            drone_pilot, drone
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        flight_ID, dir_name, flight_name, str(date),
                        folder_ID, str(start_time), str(end_time), type_,
                        num_files, num_dir, output_path, height,
                        drone_pilot, drone
                    ))
                    conn.commit()
                    st.success(f"✅ Flight log '{flight_ID}' added.")
                except sqlite3.IntegrityError:
                    st.error("❌ A log with this ID already exists.")


# ==============================================================================
# PAGE ENTRYPOINT
# ==============================================================================

# Page title
st.title("📁 Add Flight Route & Log")

# Load dropdown options
pilots, drones = get_options_from_db()

# Render forms
with st.expander("➕ Add Flight Route"):
    add_flight_route_form()

with st.expander("🛬 Add Flight Log"):
    add_flight_log_form()

initialize_drone_database(DB_PATH)