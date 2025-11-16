# ======================= DATA STORAGE MODULE =======================
# This file handles the main in-memory dataset (list or dict of records).
# Steps:
# 1. Load raw data from utils/data_loader.py
# 2. Store each record in a Python structure (e.g. list of dicts)
# 3. Build AVL indexes for key attributes (like price or rating)
# 4. Expose methods to get or modify data through indexes
# Purpose: Link raw data with AVL trees for efficient access.

from avl_tree import AVLTree



class DataStore:

    def __init__(self, index_attributes: list):
        """
        index_attributes: list of fields to index with AVL Trees.
        Example: ["user_id", "age", "rating"]
        """
        self.records = []                  # raw records (list of dicts)
        self.index_attributes = index_attributes

        # Each indexed attribute gets its own AVL tree
        self.indexes = {attr: AVLTree() for attr in index_attributes}

        # Keep track of AVL roots
        self.roots = {attr: None for attr in index_attributes}


    # ---------------------------------------------------------
    # INSERT RECORD
    # ---------------------------------------------------------
    def insert_record(self, record: dict):
        """
        Insert a new record into the raw storage and update AVL indexes.
        Returns the record_id (its index in self.records).
        """
        record_id = len(self.records)
        self.records.append(record)

        # Update each AVL index
        for attr in self.index_attributes:
            key = record[attr]
            tree = self.indexes[attr]
            root = self.roots[attr]

            # If the key already exists, append to its list of record IDs
            node = tree.search(root, key)
            if node:
                node.value.append(record_id)
            else:
                # Create a new node with a list containing this record ID
                self.roots[attr] = tree.insert(root, key, [record_id])

        return record_id


    # ---------------------------------------------------------
    # LOOKUP EXACT VALUE
    # ---------------------------------------------------------
    def search_by_attr(self, attr: str, key):
        """
        Returns list of records where record[attr] == key.
        Uses AVL index for fast lookup.
        """
        tree = self.indexes[attr]
        root = self.roots[attr]

        node = tree.search(root, key)
        if not node:
            return []

        return [self.records[rid] for rid in node.value]


    # ---------------------------------------------------------
    # RANGE QUERY
    # ---------------------------------------------------------
    def range_query(self, attr: str, low, high):
        """
        Returns all records where low <= record[attr] <= high.
        Uses in-order traversal of the AVL index.
        """
        tree = self.indexes[attr]
        root = self.roots[attr]
        result_ids = []

        def traverse(node):
            if not node:
                return
            if node.key > low:
                traverse(node.left)
            if low <= node.key <= high:
                result_ids.extend(node.value)
            if node.key < high:
                traverse(node.right)

        traverse(root)
        return [self.records[rid] for rid in result_ids]


    # ---------------------------------------------------------
    # DELETE RECORD
    # ---------------------------------------------------------
    def delete_record(self, record_id: int):
        """
        Deletes a record:
        - Removes it from AVL indexes
        - Marks it as None in raw storage
        """
        record = self.records[record_id]
        if record is None:
            return False

        # Remove from indexes
        for attr in self.index_attributes:
            key = record[attr]
            tree = self.indexes[attr]
            root = self.roots[attr]

            node = tree.search(root, key)
            if node:
                node.value.remove(record_id)
                # If node becomes empty → remove key from AVL
                if len(node.value) == 0:
                    self.roots[attr] = tree.delete(root, key)

        self.records[record_id] = None
        return True


    # ---------------------------------------------------------
    # MODIFY RECORD
    # ---------------------------------------------------------
    def update_record(self, record_id: int, new_record: dict):
        """
        Update a record:
        - Delete old record from indexes
        - Insert updated record
        """
        self.delete_record(record_id)

        # Insert and force the ID to remain the same
        self.records[record_id] = new_record

        for attr in self.index_attributes:
            key = new_record[attr]
            tree = self.indexes[attr]
            root = self.roots[attr]

            node = tree.search(root, key)
            if node:
                node.value.append(record_id)
            else:
                self.roots[attr] = tree.insert(root, key, [record_id])

        return True


    # ---------------------------------------------------------
    # GET RECORD BY ID
    # ---------------------------------------------------------
    def get_record(self, record_id: int):
        return self.records[record_id]

# Testing to see if it works correctly
if __name__ == "__main__":
    ds = DataStore(index_attributes=["age", "rating"])

    r1 = {"user_id": 1, "age": 25, "rating": 4.5}
    r2 = {"user_id": 2, "age": 30, "rating": 3.8}
    r3 = {"user_id": 3, "age": 22, "rating": 4.9}

    id1 = ds.insert_record(r1)
    id2 = ds.insert_record(r2)
    id3 = ds.insert_record(r3)

    print("Search by age 25:", ds.search_by_attr("age", 25))
    print("Range query age 20-28:", ds.range_query("age", 20, 28))

    ds.update_record(id1, {"user_id": 1, "age": 26, "rating": 4.6})
    print("After update, search by age 26:", ds.search_by_attr("age", 26))

    ds.delete_record(id2)
    print("After deletion, search by age 30:", ds.search_by_attr("age", 30))