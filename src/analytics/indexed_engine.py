# src/analytics/indexed_engine.py
import streamlit as st
from src.storage.data_store import DataStore
from src.query_engine.query_handler import QueryEngine


@st.cache_resource
def build_applications_engine(cleaned_data, max_records: int = 2_000):
    """
    Build a DataStore + QueryEngine for a *subset* of the applications table.

    Idea:
      - Full dataset is ~239k rows → heavy to index fully.
      - For UI, we only need a small demo subset.
      - We index:
          • first `max_records` apps (default 2,000)
          • only 'appid' and 'mat_final_price' attributes.

    Returns:
      (engine, apps_subset)
    """
    apps = cleaned_data.get("applications", [])

    # Limit the number of records for faster UI/demo.
    if max_records is not None and len(apps) > max_records:
        apps = apps[:max_records]

    store = DataStore(
        index_attributes=[
            "appid",           # main key for CRUD and exact lookup
            "mat_final_price", # numeric attribute for range queries
        ],
        reuse_free_slots=True,
    )

    for rec in apps:
        store.insert_record(rec)

    engine = QueryEngine(store, key_attribute="appid")
    return engine, apps


def build_indexed_engine_section(cleaned_data):
    """
    Section 2: build the indexed engine and show a small explanation.
    Returns (app_engine, indexed_apps) so later sections can use them.
    """
    st.divider()
    st.header("2. Build indexed engine (subset demo)")

    with st.spinner(
        "Building AVL indexes for a subset of applications (first run may take a bit)..."
    ):
        app_engine, indexed_apps = build_applications_engine(cleaned_data)

    st.success("Application index ready ✅")
    st.caption(
        "For UI speed, we index only the first 2,000 applications and only on 'appid' "
        "and 'mat_final_price'. The full dataset is still loaded in memory above."
    )

    return app_engine, indexed_apps
