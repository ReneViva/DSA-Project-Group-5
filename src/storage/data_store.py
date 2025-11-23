# ======================= DATA STORAGE MODULE =======================
# This file handles the main in-memory dataset (list or dict of records).
# Steps:
# 1. Load raw data from utils/data_loader.py
# 2. Store each record in a Python structure (e.g. list of dicts)
# 3. Build AVL indexes for key attributes (like price or rating)
# 4. Expose methods to get or modify data through indexes
# Purpose: Link raw data with AVL trees for efficient access.

from collections import deque

# Flexible import so this module works both inside the package (src.storage)
# and as a standalone file for testing.
try:
    from src.storage.avl_tree import AVLTree
except ImportError:  # running directly / in tests
    from avl_tree import AVLTree


class DataStore:
    """
    In-memory storage + AVL-based secondary indexes.

    - Raw records are stored in a list (self.records).
      The position in the list is the internal record_id.
    - For each indexed attribute, we maintain an AVL tree that maps:
        key -> list[record_id]

    The data store itself is intentionally low-level:
    it does NOT parse user queries. That is handled by the query engine
    (src.query_engine.query_handler).
    """

    def __init__(self, index_attributes: list, reuse_free_slots: bool = True):
        """
        :param index_attributes: list of fields to index with AVL Trees.
               Example: ["id", "name"]
        :param reuse_free_slots:
             - True  -> reuse IDs of deleted records (default)
             - False -> always append new records and never reuse freed IDs
        """
        # Raw record storage. Deleted records become None.
        self.records: list[dict | None] = []

        # Which attributes are indexed with AVL trees
        self.index_attributes = list(index_attributes)

        # One AVLTree per indexed attribute
        self.indexes: dict[str, AVLTree] = {
            attr: AVLTree() for attr in self.index_attributes
        }

        # Root node for each AVL index
        self.roots: dict[str, object | None] = {
            attr: None for attr in self.index_attributes
        }

        # Queue of IDs that have been deleted and can optionally be reused
        self.free_ids: deque[int] = deque()

        # Whether to reuse freed IDs when inserting
        self.reuse_free_slots: bool = reuse_free_slots

    # ---------------------------------------------------------
    # INSERT RECORD
    # ---------------------------------------------------------
    def insert_record(self, record: dict) -> int:
        """
        Insert a new record into raw storage and update all AVL indexes.

        Reuses a freed ID if available (and reuse_free_slots is True);
        otherwise appends to the end of the records list.

        :param record: dictionary with at least all indexed attributes present
        :return: internal record_id (index into self.records)
        """
        # Validate record contains indexed keys
        for attr in self.index_attributes:
            if attr not in record:
                raise KeyError(f"Record missing indexed attribute '{attr}'")

        # Decide which slot to use
        if self.reuse_free_slots and self.free_ids:
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
    # LOOKUP HELPERS
    # ---------------------------------------------------------
    def _get_ids_for_attr(self, attr: str, key):
        """
        Internal helper: return list of record_ids whose record[attr] == key.
        """
        if attr not in self.index_attributes:
            raise ValueError(f"Attribute '{attr}' is not indexed.")

        tree = self.indexes[attr]
        root = self.roots[attr]

        node = tree.search(root, key)
        if not node:
            return []

        ids = node.value if isinstance(node.value, list) else [node.value]
        # Filter out ids that are out of range or already deleted
        return [
            rid for rid in ids
            if 0 <= rid < len(self.records) and self.records[rid] is not None
        ]

    # ---------------------------------------------------------
    # LOOKUP EXACT VALUE (PUBLIC)
    # ---------------------------------------------------------
    def search_by_attr(self, attr: str, key):
        """
        Returns list of records where record[attr] == key.
        Uses AVL index for fast lookup.
        """
        ids = self._get_ids_for_attr(attr, key)
        return [self.records[rid] for rid in ids]

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
        result_ids: list[int] = []

        def traverse(node):
            if not node:
                return
            # Only explore left subtree if there may be keys >= low
            if node.key > low:
                traverse(node.left)
            if low <= node.key <= high:
                if isinstance(node.value, list):
                    result_ids.extend(node.value)
                else:
                    result_ids.append(node.value)
            # Only explore right subtree if there may be keys <= high
            if node.key < high:
                traverse(node.right)

        traverse(root)

        # Map IDs to records, skipping deleted slots
        return [
            self.records[rid]
            for rid in result_ids
            if 0 <= rid < len(self.records) and self.records[rid] is not None
        ]

    # ---------------------------------------------------------
    # DELETE RECORD
    # ---------------------------------------------------------
    def delete_record(self, record_id: int) -> bool:
        """
        Deletes a record by its internal ID:

        - Removes it from all AVL indexes
        - Marks the record slot as None
        - Optionally adds the ID to the free pool for reuse

        :return: True if deleted, False if invalid ID or already None.
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
                # Remove id from node.value
                if isinstance(node.value, list):
                    if record_id in node.value:
                        node.value.remove(record_id)
                else:
                    if node.value == record_id:
                        node.value = []

                # If node becomes empty → remove key from AVL
                node_empty = (
                    not node.value or
                    (isinstance(node.value, list) and len(node.value) == 0)
                )
                if node_empty:
                    self.roots[attr] = tree.delete(root, key)

        # Mark slot as deleted
        self.records[record_id] = None

        # Add to free pool only if reuse is enabled
        if self.reuse_free_slots:
            self.free_ids.append(record_id)

        return True

    # ---------------------------------------------------------
    # MODIFY RECORD
    # ---------------------------------------------------------
    def update_record(self, record_id: int, new_record: dict) -> bool:
        """
        Update a record in-place:

        - Remove old values from AVL indexes (but keep the slot)
        - Write the new record into the same slot
        - Reinsert into AVL indexes

        This keeps the record_id stable for external references.
        """
        if record_id < 0 or record_id >= len(self.records):
            raise IndexError("record_id out of range")

        # Validate new_record has indexed attributes
        for attr in self.index_attributes:
            if attr not in new_record:
                raise KeyError(f"Updated record missing indexed attribute '{attr}'")

        old_record = self.records[record_id]
        if old_record is not None:
            # Remove old record from indexes
            for attr in self.index_attributes:
                old_key = old_record[attr]
                tree = self.indexes[attr]
                root = self.roots[attr]

                node = tree.search(root, old_key)
                if node:
                    if isinstance(node.value, list):
                        if record_id in node.value:
                            node.value.remove(record_id)
                    else:
                        if node.value == record_id:
                            node.value = []

                    node_empty = (
                        not node.value or
                        (isinstance(node.value, list) and len(node.value) == 0)
                    )
                    if node_empty:
                        self.roots[attr] = tree.delete(root, old_key)

        # Overwrite the slot with new record
        self.records[record_id] = new_record

        # If this id accidentally exists in free_ids, remove it
        try:
            self.free_ids.remove(record_id)
        except ValueError:
            pass

        # Re-insert into indexes
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
        """
        Safe accessor for raw records by internal ID.
        Returns None for invalid IDs or deleted records.
        """
        if record_id < 0 or record_id >= len(self.records):
            return None
        return self.records[record_id]
