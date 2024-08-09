import streamlit as st

page_add_flights = st.Page("St_add_flights.py", title="Add drone flights")
page_review_flights = st.Page("St_review_flights.py", title="Review drone flights")
page_flight_overview = st.Page("St_field_analysis.py", title="Analysis of fields")
page_processing_stats = st.Page("St_processing_stats.py", title="Stats for processing of drone flights")

pg = st.navigation([page_add_flights, page_review_flights, page_flight_overview, page_processing_stats])
#st.set_page_config(page_title="Phenotyping", page_icon=":material/edit:") # Collides with this line on the subpages
pg.run()
