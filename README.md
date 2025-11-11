# DSA-Project-Group-5

---

# 🧠 MiniDB — Scalable In-Memory Data Management System

### *DS115 - Data Structures / Algorithms in Data Science*

### **Team:** DSA Group 5

---

## 🎯 Objective

The goal of this project is to design and implement a **lightweight, scalable, in-memory database** capable of handling large datasets efficiently.
Our MiniDB supports:

* Search, insertion, deletion, modification, and range queries
* Graph-based relationships and traversal
* Analytical operations (min, max, average, top-K)
* Manual AVL Tree indexing for efficiency
* A minimal interactive **Streamlit** UI

This project applies the core **data structures and algorithms** learned during the semester — especially **AVL Trees** and **Graph Algorithms** — to create a functional and efficient system.

---

## 📁 Folder Structure

```
MiniDB/
│
├── data/                         # Dataset files (Steam dataset or subsets)
│   ├── games.csv
│   ├── reviews.csv
│   └── developers_publishers.csv
│
├── src/
│   ├── __init__.py
│   ├── storage/                  # Core storage and indexing logic
│   │   ├── avl_tree.py           # Manual AVL tree implementation
│   │   └── data_store.py         # In-memory storage (list/dict)
│   │
│   ├── query_engine/             # CRUD and range queries
│   │   └── query_handler.py
│   │
│   ├── graph/                    # Graph-based features
│   │   ├── graph_model.py
│   │   └── graph_algorithms.py
│   │
│   ├── analytics/                # Statistical and analytical operations
│   │   └── analytics.py
│   │
│   ├── ui/                       # Streamlit frontend
│   │   └── app.py
│   │
│   └── utils/                    # Helpers, loaders, benchmarks
│       └── data_loader.py
│
├── report/
│   ├── technical_report.pdf
│   └── performance_analysis.md
│
├── README.md                     # (You are here)
└── requirements.txt
```

---

## 💻 Programming Languages & Libraries

**Primary Language:** Python 3.11+

**Libraries Used:**

* `pandas` → for data loading and preprocessing
* `numpy` → for numerical operations
* `networkx` → for graph representation and algorithms
* `streamlit` → for minimal user interface
* `matplotlib` or `plotly` → (optional) for visualizing analytics
* `time` → for performance benchmarking

---

## 📊 Dataset

### Steam Dataset 2025 — Multi-Modal Gaming Analytics

📦 Source: [Kaggle Dataset Link](https://www.kaggle.com/datasets/crainbramp/steam-dataset-2025-multi-modal-gaming-analytics)

**Description:**

* ~239,000 Steam games and 1M+ user reviews
* Covers metadata, pricing, genres, ratings, platforms, and developer–publisher networks
* 13 normalized relational tables (relational and graph-ready)
* Includes 1024-dimensional vector embeddings for semantic relationships

**Why we chose it:**

* Large-scale dataset (>1,000,000 records ✅)
* Includes both **tabular** and **graph** structures (developer ↔ publisher)
* Perfect for applying range queries, AVL indexing, and graph traversal algorithms

---

# ⚙️ Project Phases

---

## 🔹 **PHASE 1: Dataset Preparation**

### Step 1.1 — Select and Load Dataset

* Download dataset CSVs from Kaggle.
* Load into `/data` folder.
* Use `pandas` to load a manageable subset initially for testing (e.g., first 50,000 rows).

### Step 1.2 — Clean and Normalize Data

* Handle missing values, drop redundant columns.
* Ensure key attributes:
  `game_id`, `title`, `price`, `rating`, `genre`, `developer`, `publisher`, `release_year`.

### Step 1.3 — Store Raw Data

* Create a list of dictionaries:

  ```python
  [{"id": 1, "title": "Portal 2", "price": 9.99, "genre": "Puzzle", ...}, ...]
  ```
* This serves as the base layer for MiniDB.

💬 *Tip:* Start small for debugging. Use only a few thousand records until AVL and queries are stable.

---

## 🔹 **PHASE 2: Storage & Indexing Layer (AVL Tree)**

### Step 2.1 — Implement Manual AVL Tree

* Implement from scratch in `avl_tree.py`.
* Include: `insert()`, `delete()`, `search()`, and rotations (`LL`, `RR`, `LR`, `RL`).
* Keep balancing logic well-commented to demonstrate understanding.

### Step 2.2 — Integrate Index with Data Store

* In `data_store.py`, connect the raw dataset with AVL-based indexing.
* Example:

  ```python
  price_index = AVLTree()
  for record in data:
      price_index.insert(record["price"], record)
  ```
* This allows fast range queries and lookups by price or rating.

### Step 2.3 — Test AVL Tree

* Test insertion and deletion performance.
* Compare with linear search for validation.
* Print in-order traversal to verify balancing.

💬 *Comment:* AVL trees ensure **O(log n)** performance for search, insert, and delete — perfect for a large dataset.

---

## 🔹 **PHASE 3: Query Engine**

### Step 3.1 — CRUD Operations

Implement core MiniDB functions in `query_handler.py`:

* `search_record(key)`
* `insert_record(record)`
* `delete_record(key)`
* `update_record(key, field, value)`

### Step 3.2 — Range Queries

* Use AVL traversal to retrieve all records between two values.

  ```python
  results = avl.range_query(min_price=10, max_price=30)
  ```
* Return results as lists of game entries.

### Step 3.3 — Performance Testing

* Use Python’s `time` library to record operation time for each query type.
* Store results in `performance_analysis.md`.

💬 *Tip:* Demonstrate complexity comparison (e.g., AVL vs linear search) in your final report.

---

## 🔹 **PHASE 4: Graph Features**

### Step 4.1 — Graph Representation

* Use `networkx` to model relationships:

  * Nodes: Developers / Publishers
  * Edges: Collaboration (if a developer and publisher worked on the same game)

### Step 4.2 — Implement Graph Algorithms

Add functions in `graph_algorithms.py`:

* `bfs_traversal(node)`
* `dfs_traversal(node)`
* `shortest_path(dev1, dev2)`
* `connected_components()`

### Step 4.3 — Visualization (Optional)

* Use `networkx.draw()` or `plotly` to show developer–publisher networks.

💬 *Tip:* Graphs can be large — test traversal on subsets before scaling up.

---

## 🔹 **PHASE 5: Final Integration & UI**

### Step 5.1 — Build Streamlit UI

* File: `/src/ui/app.py`
* Allow users to:

  * Search by name, price, or rating
  * View range query results
  * Explore developer–publisher connections
  * Display analytics (e.g., average rating by genre)

### Step 5.2 — Integrate Analytics

* In `analytics.py`, implement:

  * `min_price()`, `max_price()`, `avg_rating()`, `median_price()`, `top_k_games(k)`
  * Optional: `knn_similar_games(title)` using embeddings

### Step 5.3 — System Integration

* Connect all layers (Data → AVL → Query Engine → Graph → UI).
* Test all workflows end-to-end:

  1. Load dataset
  2. Build indexes
  3. Run search and graph queries
  4. View analytics in UI

---

## 📈 Performance Analysis

Include in your report:

* Time complexity for search, insertion, deletion (O(log n))
* Range query complexity (O(k + log n))
* Graph traversal complexity (O(V + E))
* Benchmarks comparing indexed vs non-indexed lookups

---

## 🧩 Deliverables

✅ Fully functional MiniDB system
✅ `README.md` (this file)
✅ Technical Report (2–4 pages)
✅ Streamlit UI demo
✅ Presentation (final week)

---

## 📘 References

* Kaggle Steam Dataset 2025 — Multi-Modal Gaming Analytics
* AVL Tree algorithms (CLRS, GeeksforGeeks, and textbook references)
* NetworkX documentation
* Streamlit official docs

---

### ✅ End of README

> *Once each phase is completed and tested, push your updates to the team’s GitHub repo. Use commits like:*
> “Phase 2 Complete — Added AVL Tree and Indexing Layer.”

---

Would you like me to also prepare a **matching technical report template (2–4 pages)** with dataset schema, complexity analysis, and sample query examples next? It would pair perfectly with this README for your final submission.
