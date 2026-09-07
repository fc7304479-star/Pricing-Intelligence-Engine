import os
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
            ""
        )

        self.database = os.getenv(
            "CLICKHOUSE_DATABASE",
            "default"
        )

        print(
            f"[ClickHouse] Storage configured: "
            f"{self.host}:{self.port}/{self.database}"
        )

    # =========================================================
    # CLIENT
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
                    goods_id String,
                    product_name String,
                    product_url String,

                    price Nullable(Float64),
                    original_price Nullable(Float64),
                    discount Nullable(Float64),

                    source String,
                    currency String,
                    availability String,

                    scraped_at String,
                    stored_at String
                )
                ENGINE = MergeTree()
                ORDER BY stored_at
                """
            )

            print(
                "[ClickHouse] Products table ready"
            )

        finally:

            client.close()

    # =========================================================
    # INSERT
    # =========================================================

    def insert(self, data):

        client = self.get_client()

        try:

            price = data.get("price")

            if price is not None:
                price = float(price)

            original_price = data.get(
                "original_price"
            )

            if original_price is not None:
                original_price = float(
                    original_price
                )

            discount = data.get(
                "discount"
            )

            if discount is not None:
                discount = float(
                    discount
                )

            scraped_at = data.get(
                "scraped_at"
            )

            if not scraped_at:
                scraped_at = datetime.now(
                    timezone.utc
                ).isoformat()

            stored_at = datetime.now(
                timezone.utc
            ).isoformat()

            record = [
                str(
                    data.get(
                        "goods_id",
                        ""
                    )
                ),

                str(
                    data.get(
                        "product_name",
                        ""
                    )
                ),

                str(
                    data.get(
                        "product_url",
                        ""
                    )
                ),

                price,

                original_price,

                discount,

                str(
                    data.get(
                        "source",
                        "SHEIN"
                    )
                ),

                str(
                    data.get(
                        "currency",
                        "USD"
                    )
                ),

                str(
                    data.get(
                        "availability",
                        ""
                    )
                ),

                str(scraped_at),

                str(stored_at),
            ]

            client.insert(
                "products",
                [record],
                column_names=[
                    "goods_id",
                    "product_name",
                    "product_url",
                    "price",
                    "original_price",
                    "discount",
                    "source",
                    "currency",
                    "availability",
                    "scraped_at",
                    "stored_at",
                ],
            )

            print(
                "[ClickHouse] Stored: "
                f"{data.get('goods_id', '')} | "
                f"{data.get('product_name', '')} | "
                f"price={price}"
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
                    goods_id,
                    product_name,
                    product_url,
                    price,
                    original_price,
                    discount,
                    source,
                    currency,
                    availability,
                    scraped_at,
                    stored_at

                FROM products

                ORDER BY stored_at DESC
                """
            )

            products = []

            for row in result.result_rows:

                products.append({

                    "goods_id": row[0],

                    "product_name": row[1],

                    "product_url": row[2],

                    "price": (
                        float(row[3])
                        if row[3] is not None
                        else None
                    ),

                    "original_price": (
                        float(row[4])
                        if row[4] is not None
                        else None
                    ),

                    "discount": (
                        float(row[5])
                        if row[5] is not None
                        else None
                    ),

                    "source": row[6],

                    "currency": row[7],

                    "availability": row[8],

                    "scraped_at": row[9],

                    "stored_at": row[10],
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

            return int(
                result.result_rows[0][0]
            )

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

            print(
                "[ClickHouse] Storage Cleared"
            )

        finally:

            client.close()