# src/analytics/price_range.py
import streamlit as st


def price_range_section(app_engine):
    """
    Section 5: price range query using the AVL index on 'mat_final_price'.
    Keeps last results in st.session_state so they don't disappear.
    """
    st.divider()
    st.header("5. Range query on price (AVL-based, subset)")

    st.write(
        """
        Here we use `QueryEngine.range_query('mat_final_price', low, high)`,
        which delegates to the AVL-based `DataStore.range_query` for the price index.
        """
    )

    if "price_results" not in st.session_state:
        st.session_state.price_results = None
        st.session_state.price_last_range = (None, None)

    with st.form("price_range_form"):
        col_min, col_max = st.columns(2)
        with col_min:
            min_price = st.number_input("Min price:", value=0.0, key="min_price")
        with col_max:
            max_price = st.number_input("Max price:", value=50.0, key="max_price")

        run_price_range = st.form_submit_button("Run price range query")

    if run_price_range:
        if min_price > max_price:
            st.error("Min price cannot be greater than max price.")
            st.session_state.price_results = None
            st.session_state.price_last_range = (None, None)
        else:
            low = float(min_price)
            high = float(max_price)

            with st.spinner("Running AVL-based price range query on the subset..."):
                results = app_engine.range_query("mat_final_price", low, high)

            st.session_state.price_results = results
            st.session_state.price_last_range = (low, high)

    # Always display last results
    results = st.session_state.price_results
    low, high = st.session_state.price_last_range

    if results is not None and low is not None and high is not None:
        if not results:
            st.warning(
                f"No applications found with price between {low} and {high} in the "
                "indexed subset (first 2,000 apps)."
            )
        else:
            st.success(
                f"Found {len(results)} application(s) with price between {low} and {high}. "
                "Showing up to first 50 results:"
            )

            rows_to_show = results[:50]
            table_data = {
                "appid": [r.get("appid") for r in rows_to_show],
                "name": [r.get("name") for r in rows_to_show],
                "price": [r.get("mat_final_price") for r in rows_to_show],
            }

            st.table(table_data)
