# ======================= DATA STORAGE MODULE =======================
# This file handles the main in-memory dataset (list or dict of records).
# Steps:
# 1. Load raw data from utils/data_loader.py
# 2. Store each record in a Python structure (e.g. list of dicts)
# 3. Build AVL indexes for key attributes (like price or rating)
# 4. Expose methods to get or modify data through indexes
# Purpose: Link raw data with AVL trees for efficient access.

from collections import deque
from src.storage.avl_tree import AVLTree


class DataStore:
    def __init__(self, index_attributes: list):
        """
        index_attributes: list of fields to index with AVL Trees.
        Example: ["user_id", "age", "rating"]
        """
        self.records = []                  # raw records (list of dicts or None)
        self.index_attributes = list(index_attributes)

        # Each indexed attribute gets its own AVL tree
        self.indexes = {attr: AVLTree() for attr in self.index_attributes}

        # Keep track of AVL roots
        self.roots = {attr: None for attr in self.index_attributes}

        # Reuse freed IDs
        self.free_ids = deque()

    # ---------------------------------------------------------
    # INSERT RECORD
    # ---------------------------------------------------------
    def insert_record(self, record: dict):
        """
        Insert a new record into raw storage and update indexes.
        Reuses a freed ID if available; otherwise appends.
        Returns the record_id.
        """
        # Validate record contains indexed keys
        for attr in self.index_attributes:
            if attr not in record:
                raise KeyError(f"Record missing indexed attribute '{attr}'")

        if self.free_ids:
            record_id = self.free_ids.popleft()
            self.records[record_id] = record
        else:
            record_id = len(self.records)
            self.records.append(record)

        # Update each AVL index
        for attr in self.index_attributes:
            key = record[attr]
            tree = self.indexes[attr]
            root = self.roots[attr]

            node = tree.search(root, key)
            if node:
                # node.value is usually a list of record IDs
                if isinstance(node.value, list):
                    node.value.append(record_id)
                else:
                    node.value = [node.value, record_id]
            else:
                # Insert new node; assign the (possibly changed) root
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
        if attr not in self.index_attributes:
            raise ValueError(f"Attribute '{attr}' is not indexed.")

        tree = self.indexes[attr]
        root = self.roots[attr]

        node = tree.search(root, key)
        if not node:
            return []

        # node.value is list of record ids
        return [self.records[rid] for rid in node.value if 0 <= rid < len(self.records) and self.records[rid] is not None]

    # ---------------------------------------------------------
    # RANGE QUERY
    # ---------------------------------------------------------
    def range_query(self, attr: str, low, high):
        """
        Returns all records where low <= record[attr] <= high.
        Uses in-order traversal of the AVL index to only visit relevant keys.
        """
        if attr not in self.index_attributes:
            raise ValueError(f"Attribute '{attr}' is not indexed.")

        tree = self.indexes[attr]
        root = self.roots[attr]
        result_ids = []

        def traverse(node):
            if not node:
                return
            if node.key > low:
                traverse(node.left)
            if low <= node.key <= high:
                result_ids.extend(node.value if isinstance(node.value, list) else [node.value])
            if node.key < high:
                traverse(node.right)

        traverse(root)
        return [self.records[rid] for rid in result_ids if 0 <= rid < len(self.records) and self.records[rid] is not None]

    # ---------------------------------------------------------
    # DELETE RECORD
    # ---------------------------------------------------------
    def delete_record(self, record_id: int):
        """
        Deletes a record:
        - Removes it from AVL indexes
        - Marks it as None in raw storage
        - Adds the id to free pool for reuse
        Returns True if deleted, False if already None or invalid id.
        """
        if record_id < 0 or record_id >= len(self.records):
            return False

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
                # remove the id if present
                if isinstance(node.value, list):
                    if record_id in node.value:
                        node.value.remove(record_id)
                else:
                    if node.value == record_id:
                        node.value = []

                # If node becomes empty → remove key from AVL
                node_empty = (not node.value) or (isinstance(node.value, list) and len(node.value) == 0)
                if node_empty:
                    self.roots[attr] = tree.delete(root, key)

        # mark deleted and add to free pool
        self.records[record_id] = None
        self.free_ids.append(record_id)
        return True

    # ---------------------------------------------------------
    # MODIFY RECORD
    # ---------------------------------------------------------
    def update_record(self, record_id: int, new_record: dict):
        """
        Update a record in-place:
        - Delete old record from indexes (but keep the slot)
        - Insert updated record into same ID (so external references stay valid)
        """
        if record_id < 0 or record_id >= len(self.records):
            raise IndexError("record_id out of range")

        # Validate new_record has indexed attributes
        for attr in self.index_attributes:
            if attr not in new_record:
                raise KeyError(f"Updated record missing indexed attribute '{attr}'")

        # Delete old record (this will put id into free_ids)
        self.delete_record(record_id)

        # Overwrite the slot with new record (reusing same id)
        self.records[record_id] = new_record

        # If delete_record put the id into free_ids, remove it since we reused it
        try:
            self.free_ids.remove(record_id)
        except ValueError:
            pass  # not in free_ids

        # Re-insert into indexes (same logic as insert_record)
        for attr in self.index_attributes:
            key = new_record[attr]
            tree = self.indexes[attr]
            root = self.roots[attr]

            node = tree.search(root, key)
            if node:
                if isinstance(node.value, list):
                    node.value.append(record_id)
                else:
                    node.value = [node.value, record_id]
            else:
                self.roots[attr] = tree.insert(root, key, [record_id])

        return True

    # ---------------------------------------------------------
    # GET RECORD BY ID
    # ---------------------------------------------------------
    def get_record(self, record_id: int):
        if record_id < 0 or record_id >= len(self.records):
            return None
        return self.records[record_id]