import os
import json
from datetime import datetime

import clickhouse_connect
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


class ClickHouseStorage:

    def __init__(self):

        # ---------------------------------------
        # Environment Configuration
        # ---------------------------------------

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
            "pricing"
        )

        print(
            f"[ClickHouse] Connecting to "
            f"{self.host}:{self.port}/{self.database}"
        )

        # ---------------------------------------
        # Connect
        # ---------------------------------------

        self.client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database
        )

        print("[ClickHouse] Connected")

        self.create_table()

    # ---------------------------------------
    # Create Products Table
    # ---------------------------------------

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

        print(
            "[ClickHouse] Products table ready"
        )

    # ---------------------------------------
    # Insert Record
    # ---------------------------------------

    def insert(self, data):

        record = [

            data.get(
                "title",
                ""
            ),

            data.get(
                "url",
                ""
            ),

            float(
                data.get(
                    "price",
                    0
                )
            ),

            data.get(
                "source",
                ""
            ),

            data.get(
                "currency",
                "USD"
            ),

            json.dumps(
                data.get(
                    "network",
                    []
                )
            ),

            data.get(
                "timestamp",
                ""
            ),

            datetime.utcnow().isoformat()
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

    # ---------------------------------------
    # Get All Records
    # ---------------------------------------

    def get_all(self):

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
            ORDER BY stored_at
            """
        )

        columns = result.column_names

        return [
            dict(
                zip(columns, row)
            )
            for row in result.result_rows
        ]

    # ---------------------------------------
    # Count
    # ---------------------------------------

    def count(self):

        result = self.client.query(
            """
            SELECT count()
            FROM products
            """
        )

        return result.result_rows[0][0]

    # ---------------------------------------
    # Clear Storage
    # ---------------------------------------

    def clear(self):

        self.client.command(
            "TRUNCATE TABLE products"
        )

        print(
            "[ClickHouse] Storage Cleared"
        )