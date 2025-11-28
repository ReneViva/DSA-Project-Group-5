# src/analytics/basic_analytics.py
import streamlit as st
import statistics


def basic_analytics_section(indexed_apps):
    """
    Section 6: basic statistics (min, max, average, median)
    on the same 2,000-row subset. Uses session_state so results stay.
    """
    st.divider()
    st.header("6. Basic analytics (subset of 2,000 apps)")

    st.write(
        """
        Here we compute simple statistics (min, max, average, median) on the same
        2,000 applications that we indexed for the UI demo.
        """
    )

    if "analytics_summary" not in st.session_state:
        st.session_state.analytics_summary = None
        st.session_state.analytics_metric_key = None

    metric_label = st.selectbox(
        "Choose metric to analyze:",
        [
            "Price (mat_final_price)",
            "Metacritic score (metacritic_score)",
            "Total recommendations (recommendations_total)",
        ],
        key="metric_select",
    )

    if metric_label.startswith("Price"):
        metric_key = "mat_final_price"
    elif metric_label.startswith("Metacritic"):
        metric_key = "metacritic_score"
    else:
        metric_key = "recommendations_total"

    if st.button("Compute analytics", key="btn_compute_analytics"):
        values = [
            rec.get(metric_key)
            for rec in indexed_apps
            if rec.get(metric_key) is not None
        ]

        if not values:
            st.warning(f"No non-empty values found for '{metric_key}'.")
            st.session_state.analytics_summary = None
            st.session_state.analytics_metric_key = None
        else:
            values = [float(v) for v in values]

            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            median_val = statistics.median(values)

            st.session_state.analytics_summary = {
                "min": min_val,
                "max": max_val,
                "avg": avg_val,
                "median": median_val,
                "count": len(values),
            }
            st.session_state.analytics_metric_key = metric_key

    # Always show last computed analytics
    summary = st.session_state.analytics_summary
    metric_key_shown = st.session_state.analytics_metric_key

    if summary is not None and metric_key_shown is not None:
        st.success(
            f"Computed statistics for {summary['count']} records "
            f"on metric '{metric_key_shown}'."
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Min", f"{summary['min']:.2f}")
        col2.metric("Max", f"{summary['max']:.2f}")
        col3.metric("Average", f"{summary['avg']:.2f}")
        col4.metric("Median", f"{summary['median']:.2f}")
