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

            # -------------------------------------------------
            # ORIGINAL LEGACY TABLE
            # -------------------------------------------------

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

            # -------------------------------------------------
            # NORMALIZED PRODUCT CATALOG
            # -------------------------------------------------

            client.command(
                """
                CREATE TABLE IF NOT EXISTS product_catalog
                (
                    product_id String,
                    source String,
                    source_product_id String,
                    product_name String,
                    product_url String,
                    currency String,
                    availability String,
                    first_seen_at DateTime64(3, 'UTC'),
                    last_seen_at DateTime64(3, 'UTC'),
                    updated_at DateTime64(3, 'UTC')
                )
                ENGINE = ReplacingMergeTree(updated_at)
                ORDER BY (source, source_product_id)
                """
            )

            # -------------------------------------------------
            # NORMALIZED PRICE OBSERVATIONS
            # -------------------------------------------------

            client.command(
                """
                CREATE TABLE IF NOT EXISTS price_observations
                (
                    observation_id String,
                    product_id String,
                    source String,
                    source_product_id String,
                    price Nullable(Float64),
                    original_price Nullable(Float64),
                    discount Nullable(Float64),
                    currency String,
                    availability String,
                    observed_at DateTime64(3, 'UTC'),
                    stored_at DateTime64(3, 'UTC')
                )
                ENGINE = MergeTree()
                ORDER BY (product_id, observed_at)
                """
            )

            print(
                "[ClickHouse] Tables ready"
            )

        finally:

            client.close()

    # =========================================================
    # NORMALIZED INSERT
    # =========================================================

    def store_normalized(self, data):

        client = self.get_client()

        try:

            # -------------------------------------------------
            # BASIC VALUES
            # -------------------------------------------------

            goods_id = str(
                data.get("goods_id") or ""
            ).strip()

            source = str(
                data.get("source")
                or data.get("spider_name")
                or "SHEIN"
            ).strip()

            product_name = str(
                data.get("product_name") or ""
            ).strip()

            product_url = str(
                data.get("product_url") or ""
            ).strip()

            currency = str(
                data.get("currency") or "USD"
            ).strip()

            availability = str(
                data.get("availability") or ""
            ).strip()

            # -------------------------------------------------
            # PRODUCT IDENTITY VALIDATION
            # -------------------------------------------------

            if not goods_id:

                print(
                    "[ClickHouse] Skipped normalized item: "
                    "goods_id is empty"
                )

                return False

            product_id = (
                f"{source}-{goods_id}"
            )

            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            price = data.get("price")

            if price is not None:

                try:

                    price = float(price)

                except (TypeError, ValueError):

                    print(
                        "[ClickHouse] Invalid price for "
                        f"{product_id}: {price}"
                    )

                    price = None

            # -------------------------------------------------
            # ORIGINAL PRICE
            # -------------------------------------------------

            original_price = data.get(
                "original_price"
            )

            if original_price is not None:

                try:

                    original_price = float(
                        original_price
                    )

                except (TypeError, ValueError):

                    original_price = None

            # -------------------------------------------------
            # DISCOUNT
            # -------------------------------------------------

            discount = data.get(
                "discount"
            )

            if discount is not None:

                try:

                    discount = float(
                        discount
                    )

                except (TypeError, ValueError):

                    discount = None

            # -------------------------------------------------
            # TIMESTAMPS
            # -------------------------------------------------

            now = datetime.now(
                timezone.utc
            )

            scraped_at = data.get(
                "scraped_at"
            )

            if scraped_at:

                try:

                    observed_at = datetime.fromisoformat(
                        str(scraped_at).replace(
                            "Z",
                            "+00:00"
                        )
                    )

                    if observed_at.tzinfo is None:

                        observed_at = observed_at.replace(
                            tzinfo=timezone.utc
                        )

                    observed_at = observed_at.astimezone(
                        timezone.utc
                    )

                except (TypeError, ValueError):

                    observed_at = now

            else:

                observed_at = now

            stored_at = now

            # -------------------------------------------------
            # PRESERVE FIRST SEEN
            # -------------------------------------------------

            existing = client.query(
                """
                SELECT
                    first_seen_at
                FROM
                (
                    SELECT
                        first_seen_at,
                        updated_at
                    FROM product_catalog
                    WHERE source = {source:String}
                      AND source_product_id = {source_product_id:String}
                    ORDER BY updated_at DESC
                    LIMIT 1
                )
                LIMIT 1
                """,
                parameters={
                    "source": source,
                    "source_product_id": goods_id,
                },
            )

            if existing.result_rows:

                first_seen_at = existing.result_rows[0][0]

            else:

                first_seen_at = observed_at

            # -------------------------------------------------
            # PRODUCT CATALOG
            # -------------------------------------------------

            catalog_record = [
                product_id,
                source,
                goods_id,
                product_name,
                product_url,
                currency,
                availability,
                first_seen_at,
                observed_at,
                stored_at,
            ]

            client.insert(
                "product_catalog",
                [catalog_record],
                column_names=[
                    "product_id",
                    "source",
                    "source_product_id",
                    "product_name",
                    "product_url",
                    "currency",
                    "availability",
                    "first_seen_at",
                    "last_seen_at",
                    "updated_at",
                ],
            )

            # -------------------------------------------------
            # PRICE OBSERVATION
            # -------------------------------------------------

            if price is None:

                print(
                    "[ClickHouse] Catalog stored: "
                    f"{product_id} | "
                    f"price=None"
                )

                return True

            observation_id = (
                f"{product_id}-"
                f"{stored_at.strftime('%Y%m%d%H%M%S%f')}"
            )

            observation_record = [
                observation_id,
                product_id,
                source,
                goods_id,
                price,
                original_price,
                discount,
                currency,
                availability,
                observed_at,
                stored_at,
            ]

            client.insert(
                "price_observations",
                [observation_record],
                column_names=[
                    "observation_id",
                    "product_id",
                    "source",
                    "source_product_id",
                    "price",
                    "original_price",
                    "discount",
                    "currency",
                    "availability",
                    "observed_at",
                    "stored_at",
                ],
            )

            print(
                "[ClickHouse] Normalized stored: "
                f"{product_id} | "
                f"{product_name} | "
                f"price={price}"
            )

            return True

        finally:

            client.close()

    # =========================================================
    # ORIGINAL LEGACY INSERT
    #
    # KEPT FOR BACKWARD COMPATIBILITY
    #
    # THIS WRITES ONLY TO products
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
                "[ClickHouse] Stored legacy: "
                f"{data.get('goods_id', '')} | "
                f"{data.get('product_name', '')} | "
                f"price={price}"
            )

        finally:

            client.close()

    # =========================================================
    # GET LEGACY PRODUCTS
    #
    # KEPT FOR BACKWARD COMPATIBILITY
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
                "[ClickHouse] GET LEGACY PRODUCTS ERROR:",
                repr(e)
            )

            raise

        finally:

            client.close()

    # =========================================================
    # GET NORMALIZED PRODUCTS
    #
    # ONE LOGICAL ROW PER PRODUCT
    #
    # PRODUCT CATALOG
    # +
    # LATEST PRICE OBSERVATION
    # =========================================================

    def get_normalized_products(self):

        client = self.get_client()

        try:

            result = client.query(
                """
                SELECT
                    pc.product_id,
                    pc.source,
                    pc.source_product_id,
                    pc.product_name,
                    pc.product_url,
                    pc.currency,
                    pc.availability,
                    pc.first_seen_at,
                    pc.last_seen_at,
                    pc.updated_at,
                    latest.price,
                    latest.original_price,
                    latest.discount,
                    latest.observed_at

                FROM
                (
                    SELECT
                        product_id,
                        source,
                        source_product_id,
                        product_name,
                        product_url,
                        currency,
                        availability,
                        first_seen_at,
                        last_seen_at,
                        updated_at
                    FROM product_catalog FINAL
                ) AS pc

                LEFT JOIN
                (
                    SELECT
                        product_id,
                        price,
                        original_price,
                        discount,
                        observed_at

                    FROM
                    (
                        SELECT
                            product_id,
                            price,
                            original_price,
                            discount,
                            observed_at,

                            row_number() OVER
                            (
                                PARTITION BY product_id
                                ORDER BY observed_at DESC
                            ) AS rn

                        FROM price_observations
                    )

                    WHERE rn = 1

                ) AS latest

                ON pc.product_id = latest.product_id

                ORDER BY pc.updated_at DESC
                """
            )

            products = []

            for row in result.result_rows:

                products.append({

                    "product_id": row[0],

                    "source": row[1],

                    "source_product_id": row[2],

                    "goods_id": row[2],

                    "product_name": row[3],

                    "product_url": row[4],

                    "currency": row[5],

                    "availability": row[6],

                    "first_seen_at": str(row[7]),

                    "last_seen_at": str(row[8]),

                    "updated_at": str(row[9]),

                    "price": (
                        float(row[10])
                        if row[10] is not None
                        else None
                    ),

                    "original_price": (
                        float(row[11])
                        if row[11] is not None
                        else None
                    ),

                    "discount": (
                        float(row[12])
                        if row[12] is not None
                        else None
                    ),

                    "observed_at": (
                        str(row[13])
                        if row[13] is not None
                        else None
                    ),
                })

            return products

        except Exception as e:

            print(
                "[ClickHouse] GET NORMALIZED PRODUCTS ERROR:",
                repr(e)
            )

            raise

        finally:

            client.close()

    # =========================================================
    # GET NORMALIZED CATALOG
    # =========================================================

    def get_catalog(self):

        client = self.get_client()

        try:

            result = client.query(
                """
                SELECT
                    product_id,
                    source,
                    source_product_id,
                    product_name,
                    product_url,
                    currency,
                    availability,
                    first_seen_at,
                    last_seen_at,
                    updated_at

                FROM product_catalog FINAL

                ORDER BY updated_at DESC
                """
            )

            products = []

            for row in result.result_rows:

                products.append({

                    "product_id": row[0],

                    "source": row[1],

                    "source_product_id": row[2],

                    "goods_id": row[2],

                    "product_name": row[3],

                    "product_url": row[4],

                    "currency": row[5],

                    "availability": row[6],

                    "first_seen_at": str(row[7]),

                    "last_seen_at": str(row[8]),

                    "updated_at": str(row[9]),
                })

            return products

        finally:

            client.close()

    # =========================================================
    # GET PRICE OBSERVATIONS
    # =========================================================

    def get_observations(self):

        client = self.get_client()

        try:

            result = client.query(
                """
                SELECT
                    observation_id,
                    product_id,
                    source,
                    source_product_id,
                    price,
                    original_price,
                    discount,
                    currency,
                    availability,
                    observed_at,
                    stored_at

                FROM price_observations

                ORDER BY observed_at DESC
                """
            )

            observations = []

            for row in result.result_rows:

                observations.append({

                    "observation_id": row[0],

                    "product_id": row[1],

                    "source": row[2],

                    "source_product_id": row[3],

                    "goods_id": row[3],

                    "price": (
                        float(row[4])
                        if row[4] is not None
                        else None
                    ),

                    "original_price": (
                        float(row[5])
                        if row[5] is not None
                        else None
                    ),

                    "discount": (
                        float(row[6])
                        if row[6] is not None
                        else None
                    ),

                    "currency": row[7],

                    "availability": row[8],

                    "observed_at": str(row[9]),

                    "stored_at": str(row[10]),
                })

            return observations

        finally:

            client.close()

    # =========================================================
    # NORMALIZED PRODUCT COUNT
    # =========================================================

    def normalized_product_count(self):

        client = self.get_client()

        try:

            result = client.query(
                """
                SELECT count()
                FROM product_catalog FINAL
                """
            )

            return int(
                result.result_rows[0][0]
            )

        finally:

            client.close()

    # =========================================================
    # NORMALIZED COUNTS
    # =========================================================

    def normalized_counts(self):

        client = self.get_client()

        try:

            catalog_count = client.query(
                """
                SELECT count()
                FROM product_catalog FINAL
                """
            ).result_rows[0][0]

            observation_count = client.query(
                """
                SELECT count()
                FROM price_observations
                """
            ).result_rows[0][0]

            return {
                "catalog": int(
                    catalog_count
                ),

                "observations": int(
                    observation_count
                ),
            }

        finally:

            client.close()

    # =========================================================
    # CLEAR LEGACY TABLE ONLY
    #
    # NORMALIZED TABLES ARE NOT TOUCHED
    # =========================================================

    def clear(self):

        client = self.get_client()

        try:

            client.command(
                "TRUNCATE TABLE products"
            )

            print(
                "[ClickHouse] Legacy storage cleared"
            )

        finally:

            client.close()