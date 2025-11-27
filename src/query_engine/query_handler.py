# ======================= QUERY ENGINE =======================
# This file manages CRUD operations and range queries.
# Steps:
# 1. Define functions: insert_record(), delete_record(), update_record(), search_record()
# 2. Connect these functions to the data_store and AVL trees
# 3. Implement range_query() using AVL traversal
# 4. Optionally track performance times for testing
# Purpose: Handle all user queries and return results efficiently.
# ======================= QUERY ENGINE =======================
# This file provides a higher-level query interface on top of the
# low-level DataStore (storage + AVL indexing).
#
# Responsibilities:
#   - CRUD operations exposed in a user-friendly way
#   - Simple range queries
#   - A clean separation between storage and query logic
#
# This corresponds to PHASE 3 (Query Engine) in the project README.

from __future__ import annotations

from typing import Any, List


from src.storage.data_store import DataStore



class QueryEngine:
    """
    Thin wrapper around a single DataStore instance.

    It implements the Phase 3.1 CRUD API mentioned in the README:

        * search_record(key)
        * insert_record(record)
        * delete_record(key)
        * update_record(key, field, value)

    Here, `key` refers to the value of a chosen *primary attribute*
    (by default, "id"). For example, for the genres table that is
    typically the "id" column.

    The engine also exposes a generic range_query delegation.
    """

    def __init__(self, data_store: DataStore, key_attribute: str = "id"):
        """
        :param data_store: a DataStore instance already populated and indexed
        :param key_attribute: name of the attribute used as the logical key
                              for CRUD operations (defaults to "id")
        """
        self.store = data_store
        self.key_attribute = key_attribute

        if self.key_attribute not in self.store.index_attributes:
            raise ValueError(
                f"Key attribute '{self.key_attribute}' must be indexed in DataStore."
            )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def insert_record(self, record: dict) -> int:
        """
        Insert a new record using the underlying DataStore.

        :return: internal record_id of the inserted record.
        """
        return self.store.insert_record(record)

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------
    def search_record(self, key: Any) -> List[dict]:
        """
        Search records where primary-key-attribute == key.

        Example:
            engine.search_record(5)  # assuming key_attribute = "id"
        """
        return self.store.search_by_attr(self.key_attribute, key)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update_record(self, key: Any, field: str, value: Any) -> bool:
        """
        Update all records whose primary-key-attribute == key, by
        setting record[field] = value.

        :return: True if at least one record was updated, False otherwise.
        """
        updated_any = False
        # We rely on the AVL index to find matching records quickly
        matches = self.store.search_by_attr(self.key_attribute, key)

        if not matches:
            return False

        # We need internal record IDs to call DataStore.update_record.
        # We derive them by scanning the raw storage once.
        for record_id, rec in enumerate(self.store.records):
            if rec is None:
                continue
            if rec.get(self.key_attribute) == key:
                # Construct updated record
                new_rec = dict(rec)
                new_rec[field] = value
                self.store.update_record(record_id, new_rec)
                updated_any = True

        return updated_any

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def delete_record(self, key: Any) -> bool:
        """
        Delete all records whose primary-key-attribute == key.

        :return: True if at least one record was deleted, False otherwise.
        """
        deleted_any = False
        # Use the index to know whether matches exist
        matches = self.store.search_by_attr(self.key_attribute, key)
        if not matches:
            return False

        # Then iterate over raw storage to find and delete by internal ID
        for record_id, rec in enumerate(self.store.records):
            if rec is None:
                continue
            if rec.get(self.key_attribute) == key:
                ok = self.store.delete_record(record_id)
                deleted_any = deleted_any or ok

        return deleted_any

    # ---------------------------------------------------------
    # RANGE QUERY (DELEGATED)
    # ---------------------------------------------------------
    def range_query(self, attr: str, low: Any, high: Any) -> List[dict]:
        """
        Delegate a range query to the underlying DataStore.

        Example:
            engine.range_query("price", 10, 30)
        """
        return self.store.range_query(attr, low, high)
