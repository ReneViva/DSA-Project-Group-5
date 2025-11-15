# ======================= DATA LOADER =======================
# This file loads and cleans dataset files (CSV) into Python structures.
# Steps:
# no pandas
# 2. Handle missing values, normalize columns, and rename keys
# 3. Convert data into list of dictionaries for in-memory use
# 4. Send cleaned data to data_store.py for indexing
# Purpose: Prepare clean, ready-to-use data for the MiniDB system.

import csv
import os

class DataLoader:
    """
    Loads and cleans ALL CSV files inside /data.
    Automatically uses the schema for each file.
    """

    def __init__(self, schemas: dict, missing_default=None):
        self.schemas = schemas
        self.missing_default = missing_default

    def load_csv(self, filepath: str):
        """Reads CSV line-by-line and yields raw rows."""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def clean_value(self, raw, converter):
        """Converts string → correct type."""
        if raw is None or raw.strip() == "":
            return self.missing_default

        raw = raw.strip()

        try:
            if converter == int:
                return int(raw)
            if converter == float:
                return float(raw)
            if converter == str:
                return raw.lower()
            return converter(raw)
        except:
            return self.missing_default

    def clean_record(self, file_key, record: dict):
        """Clean row according to schema of a specific file."""
        schema = self.schemas[file_key]
        clean = {}

        for col, conv in schema.items():
            raw = record.get(col)
            clean[col] = self.clean_value(raw, conv)

        return clean

    def load_all(self, folder_path: str):
        """
        Loads and cleans every CSV in the /data folder.
        Returns dict: { file_key: [ clean rows ] }
        """
        cleaned_data = {}

        for filename in os.listdir(folder_path):
            if not filename.endswith(".csv"):
                continue

            file_key = filename.replace(".csv", "")

            if file_key not in self.schemas:
                print(f"[WARN] No schema found for {file_key}, skipping.")
                continue

            filepath = os.path.join(folder_path, filename)
            cleaned_data[file_key] = []

            for row in self.load_csv(filepath):
                clean_row = self.clean_record(file_key, row)
                cleaned_data[file_key].append(clean_row)

        return cleaned_data


