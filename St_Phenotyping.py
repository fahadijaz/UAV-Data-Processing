import streamlit as st

page_add_flights = st.Page("add_flights.py", title="Add drone flights")
page_review_flights = st.Page("review_flights.py", title="Review drone flights")
page_flight_overview = st.Page("flight_overview.py", title="Overview of drone flights")
page_processing_stats = st.Page("processing_stats.py", title="Stats for processing of drone flights")

pg = st.navigation([page_add_flights, page_review_flights, page_flight_overview, page_processing_stats])
#st.set_page_config(page_title="Phenotyping", page_icon=":material/edit:") # Collides with this line on the subpages
pg.run()