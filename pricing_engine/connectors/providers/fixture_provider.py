from datetime import datetime, timezone

from pricing_engine.connectors.providers.base_provider import (
    BaseProductProvider,
)


class FixtureProductProvider(BaseProductProvider):
    """
    Shared fixture provider for development and testing.

    This provider intentionally contains deterministic product data.

    It allows the complete acquisition pipeline to be tested without
    depending on retailer websites, API credentials, rate limits,
    or anti-bot systems.
    """

    FIXTURES = {
        "AMAZON": [
            {
                "source_product_id": "FIXTURE-AMZ-001",
                "product_name": "Sony WH-1000XM5 Wireless Headphones",
                "brand": "Sony",
                "model": "WH-1000XM5",
                "gtin": "0194252777421",
                "sku": "AMZ-WH1000XM5",
                "price": 349.00,
                "original_price": 399.00,
                "discount": 12.53,
                "currency": "USD",
                "product_url": "https://www.amazon.com/",
                "availability": "in_stock",
                "category": "consumer_electronics",
            }
        ],

        "WALMART": [
            {
                "source_product_id": "FIXTURE-WMT-001",
                "product_name": "Sony WH 1000XM5 Wireless Headphones",
                "brand": "Sony",
                "model": "WH 1000XM5",
                "gtin": "0194252777421",
                "sku": "WMT-WH1000XM5",
                "price": 339.00,
                "original_price": 399.00,
                "discount": 15.04,
                "currency": "USD",
                "product_url": "https://www.walmart.com/",
                "availability": "in_stock",
                "category": "consumer_electronics",
            }
        ],

        "BESTBUY": [
            {
                "source_product_id": "FIXTURE-BBY-001",
                "product_name": "Sony WH-1000XM5 Wireless Headphones",
                "brand": "Sony",
                "model": "WH-1000XM5",
                "gtin": "0194252777421",
                "sku": "BBY-WH1000XM5",
                "price": 349.00,
                "original_price": 399.00,
                "discount": 12.53,
                "currency": "USD",
                "product_url": "https://www.bestbuy.com/",
                "availability": "in_stock",
                "category": "consumer_electronics",
            }
        ],
    }

    def __init__(self, source):
        self.SOURCE = str(source or "").strip().upper()

        super().__init__()

    def _build_product(self, product):
        data = dict(product)

        data["source"] = self.SOURCE
        data["observed_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        return data

    def fetch_products(
        self,
        query=None,
        limit=10,
        **kwargs,
    ):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        if limit < 1:
            limit = 1

        products = self.FIXTURES.get(
            self.SOURCE,
            [],
        )

        query = str(query or "").strip().lower()

        if query:
            filtered = []

            for product in products:
                searchable_text = " ".join(
                    [
                        str(product.get("product_name") or ""),
                        str(product.get("brand") or ""),
                        str(product.get("model") or ""),
                        str(product.get("category") or ""),
                    ]
                ).lower()

                if query in searchable_text:
                    filtered.append(product)

            products = filtered

        return [
            self._build_product(product)
            for product in products[:limit]
        ]

    def fetch_product(
        self,
        source_product_id,
        **kwargs,
    ):
        source_product_id = str(
            source_product_id or ""
        ).strip()

        if not source_product_id:
            raise ValueError(
                "source_product_id is required"
            )

        products = self.fetch_products(
            query=None,
            limit=100,
        )

        for product in products:
            if (
                product["source_product_id"]
                == source_product_id
            ):
                return product

        return None