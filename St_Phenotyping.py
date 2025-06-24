import streamlit as st

page_add_flights = st.Page(r"pages/1_Add_Route_and_Log.py", title="Add flight routes and logs")
page_sdcard_import = st.Page(r"pages/2_St_add_flights.py", title="Add drone flights")
page_review_flights = st.Page(r"pages/3_St_review_flights.py", title="Review drone flights")
page_flight_overview = st.Page(r"pages/4_St_field_analysis.py", title="Analyze fields")
page_processing_stats = st.Page(r"pages/5_St_weekly_overview.py", title="Weekly Overview")

pg = st.navigation([page_add_flights, page_sdcard_import, page_review_flights, page_flight_overview, page_processing_stats])
#st.set_page_config(page_title="Phenotyping", page_icon=":material/edit:") # Collides with this line on the subpages
pg.run()
