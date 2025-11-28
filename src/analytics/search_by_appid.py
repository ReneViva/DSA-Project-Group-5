# src/analytics/search_by_appid.py
import streamlit as st


def search_by_appid_section(app_engine):
    """
    Section 3: search applications by appid using the indexed engine.
    Uses st.session_state so results stay visible even after other sections run.
    """
    st.divider()
    st.header("3. Search applications by appid (indexed)")

    # Make sure we have a place to store the last result
    if "appid_results" not in st.session_state:
        st.session_state.appid_results = None
        st.session_state.appid_last_query = None

    appid_input = st.number_input(
        "Enter appid (integer):",
        min_value=0,
        step=1,
        value=0,
        format="%d",
        key="appid_input",
    )

    if st.button("Search by appid", key="btn_search_appid"):
        results = app_engine.search_record(int(appid_input))
        st.session_state.appid_results = results
        st.session_state.appid_last_query = int(appid_input)

    # Always display whatever is stored in session_state
    results = st.session_state.appid_results
    last_q = st.session_state.appid_last_query

    if results is not None:
        if not results:
            st.warning(
                f"No application found with appid = {last_q} "
                "in the indexed subset (first 2,000 rows). "
                "It may still exist in the full dataset."
            )
        else:
            st.write(f"Found {len(results)} record(s) for appid = {last_q}:")
            st.json(results[0])
