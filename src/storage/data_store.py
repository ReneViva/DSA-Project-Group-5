# ======================= DATA STORAGE MODULE =======================
# This file handles the main in-memory dataset (list or dict of records).
# Steps:
# 1. Load raw data from utils/data_loader.py
# 2. Store each record in a Python structure (e.g. list of dicts)
# 3. Build AVL indexes for key attributes (like price or rating)
# 4. Expose methods to get or modify data through indexes
# Purpose: Link raw data with AVL trees for efficient access.
