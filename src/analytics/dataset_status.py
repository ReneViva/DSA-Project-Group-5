# src/analytics/dataset_status.py
import streamlit as st


def show_dataset_status(cleaned_data):
    """
    Section 1: show which tables we loaded and how many rows each has.
    """
    st.divider()
    st.header("1. Dataset Status")

    summary_rows = []
    for name, rows in cleaned_data.items():
        try:
            n_rows = len(rows)
        except TypeError:
            n_rows = "?"
        summary_rows.append((name, n_rows))

    st.write("**Tables loaded:**")
    st.table(
        {
            "Table": [name for name, _ in summary_rows],
            "Number of rows": [n for _, n in summary_rows],
        }
    )
