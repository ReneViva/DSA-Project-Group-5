# src/analytics/search_by_name.py
import streamlit as st


def search_by_name_section(indexed_apps):
    """
    Section 4: search applications by name within the indexed subset.
    Uses st.session_state so results stay visible.
    """
    st.divider()
    st.header("4. Search applications by name (subset, case-insensitive)")

    st.write(
        """
        Our DataLoader converts all text columns to lowercase when loading.
        Here we:
          • lowercase the user input,
          • linearly scan the *same 2,000-row subset* used for the index.
        """
    )

    if "name_results" not in st.session_state:
        st.session_state.name_results = None
        st.session_state.name_last_query = ""

    raw_name_input = st.text_input(
        "Enter application name (exact match within the subset, case-insensitive):",
        value="",
        placeholder="e.g. Team Fortress Classic",
        key="name_input",
    )

    if st.button("Search by name", key="btn_search_name"):
        user_query = raw_name_input.strip()

        if not user_query:
            st.warning("Please type a non-empty name.")
            st.session_state.name_results = None
            st.session_state.name_last_query = ""
        else:
            normalized = user_query.lower()
            results = [
                rec for rec in indexed_apps
                if rec.get("name") == normalized
            ]
            st.session_state.name_results = results
            st.session_state.name_last_query = user_query

    # Always show whatever is stored
    results = st.session_state.name_results
    last_q = st.session_state.name_last_query

    if results is not None:
        if not results:
            st.warning(
                f"No applications found with name = '{last_q}' "
                "in the first 2,000 apps. It may still exist in the full dataset."
            )
        else:
            st.success(
                f"Found {len(results)} application(s) with name '{last_q}'. "
                "Showing up to first 20:"
            )

            rows_to_show = results[:20]
            table_data = {
                "appid": [r.get("appid") for r in rows_to_show],
                "name": [r.get("name") for r in rows_to_show],
                "price": [r.get("mat_final_price") for r in rows_to_show],
            }

            st.table(table_data)
