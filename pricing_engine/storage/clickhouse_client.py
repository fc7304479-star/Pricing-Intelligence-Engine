import os
import json
from datetime import datetime, timezone

import clickhouse_connect
from dotenv import load_dotenv


load_dotenv()


class ClickHouseStorage:

    def __init__(self):
        self.host = os.getenv("CLICKHOUSE_HOST", "127.0.0.1")
        self.port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
        self.username = os.getenv("CLICKHOUSE_USER", "default")
        self.password = os.getenv("CLICKHOUSE_PASSWORD", "")
        self.database = os.getenv("CLICKHOUSE_DATABASE", "default")

        print(
            f"[ClickHouse] Storage configured: "
            f"{self.host}:{self.port}/{self.database}"
        )

    # =========================================================
    # NEW CLIENT PER OPERATION
    # =========================================================

    def get_client(self):

        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
            connect_timeout=15,
            send_receive_timeout=30,
        )

    # =========================================================
    # CREATE TABLE
    # =========================================================

    def create_table(self):

        client = self.get_client()

        try:

            client.command(
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

        finally:

            client.close()

    # =========================================================
    # INSERT
    # =========================================================

    def insert(self, data):

        client = self.get_client()

        try:

            network = data.get("network", [])

            if network is None:
                network = []

            if not isinstance(network, str):
                network = json.dumps(network)

            timestamp = data.get("timestamp", "")

            if timestamp is None:
                timestamp = ""

            record = [
                str(data.get("title", "")),
                str(data.get("url", "")),
                float(data.get("price", 0)),
                str(data.get("source", "")),
                str(data.get("currency", "USD")),
                network,
                str(timestamp),
                datetime.now(timezone.utc).isoformat(),
            ]

            client.insert(
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
                    "stored_at",
                ],
            )

            print(
                f"[ClickHouse] Stored: "
                f"{data.get('title', '')}"
            )

        finally:

            client.close()

    # =========================================================
    # GET ALL
    # =========================================================

    def get_all(self):

        client = self.get_client()

        try:

            result = client.query(
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

            products = []

            for row in result.result_rows:

                products.append({
                    "title": row[0],
                    "url": row[1],
                    "price": float(row[2]),
                    "source": row[3],
                    "currency": row[4],
                    "network": row[5],
                    "timestamp": row[6],
                    "stored_at": row[7],
                })

            return products

        except Exception as e:

            print(
                "[ClickHouse] GET PRODUCTS ERROR:",
                repr(e)
            )

            raise

        finally:

            client.close()

    # =========================================================
    # COUNT
    # =========================================================

    def count(self):

        client = self.get_client()

        try:

            result = client.query(
                """
                SELECT count()
                FROM products
                """
            )

            return int(result.result_rows[0][0])

        finally:

            client.close()

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        client = self.get_client()

        try:

            client.command(
                "TRUNCATE TABLE products"
            )

            print("[ClickHouse] Storage Cleared")

        finally:

            client.close()