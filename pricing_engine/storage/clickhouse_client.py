import json
from pathlib import Path
from datetime import datetime


class ClickHouseStorage:

    def __init__(self):

        self.output_dir = Path("output")

        self.output_dir.mkdir(exist_ok=True)

        self.storage_file = (
            self.output_dir / "clickhouse_storage.json"
        )

    # ---------------------------------------
    # Insert Record
    # ---------------------------------------

    def insert(self, data):

        records = []

        if self.storage_file.exists():

            try:

                with open(
                    self.storage_file,
                    "r",
                    encoding="utf-8",
                ) as f:

                    records = json.load(f)

            except Exception:

                records = []

        data["stored_at"] = (
            datetime.utcnow().isoformat()
        )

        records.append(data)

        with open(
            self.storage_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                records,
                f,
                indent=4,
                ensure_ascii=False,
            )

        print(
            f"[ClickHouse] Stored : {data['title']}"
        )

    # ---------------------------------------
    # Read All Records
    # ---------------------------------------

    def get_all(self):

        if not self.storage_file.exists():

            return []

        try:

            with open(
                self.storage_file,
                "r",
                encoding="utf-8",
            ) as f:

                return json.load(f)

        except Exception:

            return []

    # ---------------------------------------
    # Count
    # ---------------------------------------

    def count(self):

        return len(self.get_all())

    # ---------------------------------------
    # Clear Storage
    # ---------------------------------------

    def clear(self):

        with open(
            self.storage_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump([], f)

        print("[ClickHouse] Storage Cleared")