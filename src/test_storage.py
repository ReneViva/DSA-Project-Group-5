# src/test_storage.py
from src.utils.data_loader import DataLoader
from src.storage.data_store import DataStore
from src.utils.schemas import SCHEMAS

def main():
    loader = DataLoader(SCHEMAS)
    cleaned = loader.load_all("data")
    genres = cleaned.get("genres", [])
    print(f"Loaded {len(genres)} genres.")

    # Use reuse_free_slots=True to reuse deleted IDs (set False to always append)
    store = DataStore(index_attributes=["id", "name"], reuse_free_slots=True)

    # Insert all genres
    for record in genres:
        store.insert_record(record)
    print("Inserted into DataStore.")

    print("\n=== Search by name 'strategy' ===")
    results = store.search_by_attr("name", "strategy")
    print(results)

    print("\n=== Genres with id between 10 and 20 ===")
    ranged = store.range_query("id", 10, 20)
    print("Found:", len(ranged))
    for r in ranged[:10]:
        print(r)

    print("\n=== Delete record 0 ===")
    ok = store.delete_record(0)
    print("Deleted:", ok)
    print("Record 0 now:", store.get_record(0))

    new_id = store.insert_record(genres[0])
    print("Reinserted at ID:", new_id)
    print("Record at reinserted ID:", store.get_record(new_id))
    print("=== End of DataStore test ===")

if __name__ == "__main__":
    main()

