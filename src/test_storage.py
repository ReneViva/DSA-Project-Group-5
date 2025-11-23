from src.utils.data_loader import DataLoader
from src.storage.data_store import DataStore
from src.utils.schemas import SCHEMAS

# 1) Load CSV files
loader = DataLoader(SCHEMAS)
cleaned = loader.load_all("data")

genres = cleaned["genres"]
print(f"Loaded {len(genres)} genres.")

# 2) Create DataStore with indexes on id and name
store = DataStore(index_attributes=["id", "name"])

# 3) Insert all records
for record in genres:
    store.insert_record(record)
print("Inserted into DataStore.")

# 4) Test exact search
print("\n=== Search by name 'strategy' ===")
results = store.search_by_attr("name", "strategy")
print(results)

# 5) Range query
print("\n=== Genres with id between 10 and 20 ===")
ranged = store.range_query("id", 10, 20)
print("Found:", len(ranged))
for r in ranged[:5]:
    print(r)

# 6) Test delete
print("\n=== Delete record 0 ===")
store.delete_record(0)
print("Record 0 now:", store.get_record(0))

# Reinsert manually
new_id = store.insert_record(genres[0])
print("Reinserted at new ID:", new_id)
print("Record at new ID:", store.get_record(new_id))

print("\n=== Done ===")
