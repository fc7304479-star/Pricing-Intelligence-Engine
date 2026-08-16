import os
import json
from datetime import datetime, timezone

import clickhouse_connect
from dotenv import load_dotenv


load_dotenv()


class ClickHouseStorage:

    def __init__(self):

        self.host = os.getenv(
            "CLICKHOUSE_HOST",
            "127.0.0.1"
        )

        self.port = int(
            os.getenv(
                "CLICKHOUSE_PORT",
                "8123"
            )
        )

        self.username = os.getenv(
            "CLICKHOUSE_USER",
            "default"
        )

        self.password = os.getenv(
            "CLICKHOUSE_PASSWORD",
            "pricing123"
        )

        self.database = os.getenv(
            "CLICKHOUSE_DATABASE",
            "default"
        )

        print(
            f"[ClickHouse] Connecting to "
            f"{self.host}:{self.port}/{self.database}"
        )

        self.client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
            secure=True
        )

        print("[ClickHouse] Connected")

        self.create_table()

    # ---------------------------------------------------
    # Create Table
    # ---------------------------------------------------

    def create_table(self):

        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS products
            (
                title String,
                url String,
                price Float64,
                source String,
                currency String,
                network String,
                timestamp String,
                stored_at String
            )
            ENGINE = MergeTree()
            ORDER BY stored_at
            """
        )

        print("[ClickHouse] Products table ready")

    # ---------------------------------------------------
    # Insert
    # ---------------------------------------------------

    def insert(self, data):

        record = [
            str(data.get("title", "")),
            str(data.get("url", "")),
            float(data.get("price", 0)),
            str(data.get("source", "")),
            str(data.get("currency", "USD")),
            json.dumps(data.get("network", [])),
            str(data.get("timestamp", "")),
            datetime.now(timezone.utc).isoformat()
        ]

        self.client.insert(
            "products",
            [record],
            column_names=[
                "title",
                "url",
                "price",
                "source",
                "currency",
                "network",
                "timestamp",
                "stored_at"
            ]
        )

        print(
            f"[ClickHouse] Stored: "
            f"{data.get('title', '')}"
        )

    # ---------------------------------------------------
    # Get All
    # ---------------------------------------------------

    def get_all(self):

        print("[ClickHouse] Fetching products")

        result = self.client.query(
            """
            SELECT
                title,
                url,
                price,
                source,
                currency,
                network,
                timestamp,
                stored_at
            FROM products
            ORDER BY stored_at DESC
            """
        )

        columns = result.column_names

        products = []

        for row in result.result_rows:

            item = dict(
                zip(columns, row)
            )

            # Make sure API receives JSON-safe values
            item["title"] = str(item.get("title", ""))
            item["url"] = str(item.get("url", ""))
            item["price"] = float(item.get("price", 0))
            item["source"] = str(item.get("source", ""))
            item["currency"] = str(item.get("currency", ""))
            item["network"] = str(item.get("network", ""))
            item["timestamp"] = str(item.get("timestamp", ""))
            item["stored_at"] = str(item.get("stored_at", ""))

            products.append(item)

        print(
            f"[ClickHouse] Retrieved "
            f"{len(products)} products"
        )

        return products

    # ---------------------------------------------------
    # Count
    # ---------------------------------------------------

    def count(self):

        result = self.client.query(
            """
            SELECT count()
            FROM products
            """
        )

        return int(result.result_rows[0][0])

    # ---------------------------------------------------
    # Clear
    # ---------------------------------------------------

    def clear(self):

        self.client.command(
            "TRUNCATE TABLE products"
        )

        print("[ClickHouse] Storage Cleared")