from src.utils.data_loader import DataLoader
from src.storage.data_store import DataStore
from src.utils.schemas import SCHEMAS
# ================================
# 1. Define schemas for your CSV
# ================================


# ================================
# 2. Load CSV
# ================================
loader = DataLoader(SCHEMAS)
cleaned = loader.load_all("data")   # folder where your csvs are

genres = cleaned["genres"]
print(f"Loaded {len(genres)} genres.")

# ================================
# 3. Create DataStore with Indexes
# ================================
store = DataStore(index_attributes=["id", "name"])

# Insert all genres
for record in genres:
    store.insert_record(record)

print("Inserted into DataStore.")


# ================================
# 4. Test EXACT SEARCH
# ================================
print("\n=== Search name 'strategy' ===")
results = store.search_by_attr("Racing", "name")
print(results)


# ================================
# 5. Test RANGE QUERY
# ================================
print("\n=== Products with id between 10 and 20 ===")
ranged = store.range_query("id", 10, 20)
print("Found:", len(ranged))
for r in ranged:   # print only first 5
    print(r)


# ================================
# 6. Test DELETE
# ================================
print("\n=== Delete record 0 ===")
store.delete_record(0)
print("Record 0:", store.get_record(0))
store.insert_record(genres[0])  # re-insert
print("Re-inserted Record 0:", store.get_record(0))



print("\n=== Done ===")
