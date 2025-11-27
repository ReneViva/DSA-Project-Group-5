import os
import sys
import statistics

# === Make sure Python can find our project ===
# These lines add the project root (DSA-Project-Group-5) to sys.path so
# that imports like "from src.utils..." work both in VS Code and Streamlit.
CURRENT_DIR = os.path.dirname(__file__)          # .../src/ui
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))  # .../DSA-Project-Group-5
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

# Our own project modules
from src.utils.data_loader import DataLoader
from src.utils.schemas import SCHEMAS
from src.storage.data_store import DataStore
from src.query_engine.query_handler import QueryEngine


# === Cached helpers ===
@st.cache_data
def load_clean_data():
    """Load and clean all CSVs using DataLoader + SCHEMAS.

    This is the *expensive* CSV loading step (reading all CSV files, typing
    columns, lowercasing strings, etc.). Streamlit's @st.cache_data makes
    sure we only do it once per code change.
    """
    loader = DataLoader(SCHEMAS)
    cleaned = loader.load_all("data")  # assumes /data folder in project root
    return cleaned


@st.cache_resource
def build_applications_engine(cleaned_data, max_records: int = 2_000):
    """Build a DataStore + QueryEngine for a *subset* of the applications table.

    Important performance idea:
    ---------------------------
    Building AVL indexes for all ~239k rows and multiple attributes is heavy.
    For an interactive UI, we don't actually need the *full* dataset indexed.

    So for the UI demo we:
      • take only the first `max_records` applications (default = 2,000)
      • build AVL indexes only on:
          - appid          → fast CRUD / primary-key search
          - mat_final_price→ fast range queries on price

    The full cleaned dataset is still available in `cleaned_data`, but the
    heavy AVL-based DataStore is created only for this smaller subset to
    keep the app responsive.
    """

    apps = cleaned_data.get("applications", [])

    # Limit the number of records for faster UI during demo / development.
    if max_records is not None and len(apps) > max_records:
        apps = apps[:max_records]

    # Create DataStore with AVL indexes for the attributes we care about *in the UI*.
    store = DataStore(
        index_attributes=[
            "appid",           # main key for CRUD and exact lookup
            "mat_final_price", # numeric attribute for range queries
        ],
        reuse_free_slots=True,
    )

    # Insert all selected application records into the DataStore
    for rec in apps:
        store.insert_record(rec)

    # Wrap the DataStore with the QueryEngine using appid as the logical key
    engine = QueryEngine(store, key_attribute="appid")
    return engine, apps  # we also return the subset of apps we indexed


# === Streamlit UI ===
st.set_page_config(
    page_title="DSA Project – Steam Apps Explorer",
    layout="wide",
)

st.title("DSA Project – Steam Apps Explorer")
st.subheader("UI Phase 🚀")

st.write(
    """
    If you can see this message in the browser, then:
    - Python ✅
    - Streamlit ✅
    - app.py wired correctly ✅
    """
)

st.divider()

# ---------------------------------------------------------------------------
# 1. Dataset status
# ---------------------------------------------------------------------------
st.header("1. Dataset Status")

with st.spinner("Loading and cleaning CSV files..."):
    cleaned_data = load_clean_data()

st.success("Data loaded successfully! 🎉")

# Build a small summary table of table names and row counts
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

# ---------------------------------------------------------------------------
# 2. Build the indexed engine (small, fast subset)
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Build indexed engine (subset demo)")

with st.spinner("Building AVL indexes for a subset of applications (first run may take a bit)..."):
    app_engine, indexed_apps = build_applications_engine(cleaned_data)

st.success("Application index ready ✅")
st.caption(
    "For UI speed, we index only the first 2,000 applications and only on 'appid' "
    "and 'mat_final_price'. The full dataset is still loaded in memory above."
)

# ---------------------------------------------------------------------------
# 3. Search applications by appid (uses AVL index)
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Search applications by appid (indexed)")

appid_input = st.number_input(
    "Enter appid (integer):",
    min_value=0,
    step=1,
    value=0,
    format="%d",
)

if st.button("Search by appid"):
    results = app_engine.search_record(int(appid_input))

    if not results:
        st.warning(
            f"No application found with appid = {int(appid_input)} in the indexed subset "
            "(first 2,000 rows). It may still exist in the full dataset."
        )
    else:
        st.write(f"Found {len(results)} record(s):")
        # Show the first record in a nice JSON format.
        st.json(results[0])

# ---------------------------------------------------------------------------
# 4. Search applications by name (case-insensitive, linear over subset)
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Search applications by name (subset, case-insensitive)")

st.write(
    """
    Our DataLoader converts all text columns to lowercase when loading.
    Here we:
      • lowercase the user input,
      • linearly scan the *same 2,000-row subset* used for the index.

    This keeps the code simple and very fast for the UI, while the heavy
    indexing logic is still demonstrated above for appid and price.
    """
)

raw_name_input = st.text_input(
    "Enter application name (exact match within the subset, case-insensitive):",
    value="",
    placeholder="e.g. Team Fortress Classic",
)

if st.button("Search by name"):
    user_query = raw_name_input.strip()

    if not user_query:
        st.warning("Please type a non-empty name.")
    else:
        normalized = user_query.lower()

        # Linear scan over the same subset we indexed (indexed_apps)
        results = [rec for rec in indexed_apps if rec.get("name") == normalized]

        if not results:
            st.warning(
                f"No applications found with name = '{user_query}' in the first 2,000 apps. "
                "It may still exist in the full dataset."
            )
        else:
            st.success(f"Found {len(results)} application(s). Showing up to first 20:")

            rows_to_show = results[:20]

            table_data = {
                "appid": [r.get("appid") for r in rows_to_show],
                "name": [r.get("name") for r in rows_to_show],
                "price": [r.get("mat_final_price") for r in rows_to_show],
            }

            st.table(table_data)

# ---------------------------------------------------------------------------
# 5. Range query on price (uses AVL index on mat_final_price)
# ---------------------------------------------------------------------------
st.divider()
st.header("5. Range query on price (AVL-based, subset)")

st.write(
    """
    Here we use `QueryEngine.range_query('mat_final_price', low, high)`, which
    delegates to the AVL-based `DataStore.range_query` for the price index.

    Again, this operates on the same 2,000-row subset that we indexed in order
    to keep the UI responsive.
    """
)

with st.form("price_range_form"):
    col_min, col_max = st.columns(2)
    with col_min:
        min_price = st.number_input("Min price:", value=0.0)
    with col_max:
        max_price = st.number_input("Max price:", value=50.0)

    run_price_range = st.form_submit_button("Run price range query")

if run_price_range:
    if min_price > max_price:
        st.error("Min price cannot be greater than max price.")
    else:
        low = float(min_price)
        high = float(max_price)

        with st.spinner("Running AVL-based price range query on the subset..."):
            results = app_engine.range_query("mat_final_price", low, high)

        if not results:
            st.warning(
                f"No applications found with price between {low} and {high} in the "
                "indexed subset (first 2,000 apps)."
            )
        else:
            st.success(
                f"Found {len(results)} application(s). Showing up to first 50 results:"
            )

            rows_to_show = results[:50]

            table_data = {
                "appid": [r.get("appid") for r in rows_to_show],
                "name": [r.get("name") for r in rows_to_show],
                "price": [r.get("mat_final_price") for r in rows_to_show],
            }

            st.table(table_data)


# ---------------------------------------------------------------------------
# 6. Basic analytics on the indexed subset
# ---------------------------------------------------------------------------
st.divider()
st.header("6. Basic analytics (subset of 2,000 apps)")

st.write(
    """
    Here we compute simple statistics (min, max, average, median) on the same
    2,000 applications that we indexed for the UI demo.

    This shows an example of the kind of analytics the system can support.
    """
)

metric_label = st.selectbox(
    "Choose metric to analyze:",
    [
        "Price (mat_final_price)",
        "Metacritic score (metacritic_score)",
        "Total recommendations (recommendations_total)",
    ],
)

if metric_label.startswith("Price"):
    metric_key = "mat_final_price"
elif metric_label.startswith("Metacritic"):
    metric_key = "metacritic_score"
else:
    metric_key = "recommendations_total"

if st.button("Compute analytics"):
    # Extract the chosen metric from the indexed subset and drop missing values
    values = [
        rec.get(metric_key)
        for rec in indexed_apps
        if rec.get(metric_key) is not None
    ]

    if not values:
        st.warning(f"No non-empty values found for '{metric_key}'.")
    else:
        # Make sure everything is numeric (just in case)
        values = [float(v) for v in values]

        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        median_val = statistics.median(values)

        st.success(
            f"Computed statistics for {len(values)} records "
            f"on metric '{metric_key}'."
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Min", f"{min_val:.2f}")
        col2.metric("Max", f"{max_val:.2f}")
        col3.metric("Average", f"{avg_val:.2f}")
        col4.metric("Median", f"{median_val:.2f}")
