from datetime import datetime, timezone

from pricing_engine.connectors.base_connector import (
    BaseProductConnector,
)


class BestBuyConnector(BaseProductConnector):
    """
    Best Buy product connector.

    This connector currently provides the common Best Buy
    product interface and a safe fixture mode for testing.

    Live Best Buy collection will be added separately after
    the connector contract is verified.
    """

    SOURCE = "BESTBUY"

    def __init__(
        self,
        use_fixture=False,
    ):
        super().__init__()

        self.use_fixture = use_fixture

    # =========================================================
    # FETCH PRODUCTS
    # =========================================================

    def fetch_products(
        self,
        query=None,
        limit=10,
        **kwargs,
    ):
        """
        Fetch Best Buy products.

        Current implementation supports fixture mode only.

        Live Best Buy collection will be connected later
        without changing the common product schema.
        """

        if not self.use_fixture:
            raise NotImplementedError(
                "Live Best Buy collection is not enabled yet"
            )

        query = (
            str(query or "consumer electronics")
            .strip()
        )

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError,
        ):
            limit = 10

        if limit < 1:
            limit = 1

        products = []

        fixture_products = [
            {
                "source_product_id": "FIXTURE-BBY-001",
                "product_name": (
                    "Sony WH-1000XM5 Wireless "
                    "Headphones"
                ),
                "brand": "Sony",
                "model": "WH-1000XM5",
                "gtin": "0194252777421",
                "sku": "BBY-WH1000XM5",
                "price": 349.00,
                "original_price": 399.00,
                "discount": 12.53,
                "currency": "USD",
                "product_url": (
                    "https://www.bestbuy.com/"
                ),
                "availability": "in_stock",
                "category": "consumer_electronics",
                "observed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        ]

        for product in fixture_products[:limit]:

            product["search_query"] = query

            products.append(
                self.prepare_product(
                    product
                )
            )

        return products

    # =========================================================
    # FETCH ONE PRODUCT
    # =========================================================

    def fetch_product(
        self,
        source_product_id,
        **kwargs,
    ):
        """
        Fetch one Best Buy product.

        Current implementation supports fixture mode only.
        """

        source_product_id = str(
            source_product_id or ""
        ).strip()

        if not source_product_id:
            raise ValueError(
                "source_product_id is required"
            )

        if not self.use_fixture:
            raise NotImplementedError(
                "Live Best Buy collection is not enabled yet"
            )

        products = self.fetch_products(
            query="consumer electronics",
            limit=10,
        )

        for product in products:

            if (
                product["source_product_id"]
                == source_product_id
            ):
                return product

        return None