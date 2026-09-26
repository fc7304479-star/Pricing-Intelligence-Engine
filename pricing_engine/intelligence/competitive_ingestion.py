from pricing_engine.connectors.amazon.connector import AmazonConnector
from pricing_engine.connectors.walmart.connector import WalmartConnector
from pricing_engine.connectors.bestbuy.connector import BestBuyConnector

from pricing_engine.intelligence.competitive_persistence import (
    CompetitivePersistenceService,
)


class CompetitiveIngestionService:
    """
    End-to-end ingestion service for the competitive pricing MVP.

    Current sources:
        AMAZON
        WALMART
        BESTBUY

    Amazon is currently treated as the reference/baseline source.

    The ingestion service coordinates:
        connectors
            ↓
        source products
            ↓
        persistence
            ↓
        canonical matching
            ↓
        historical observations
    """

    REFERENCE_SOURCE = "AMAZON"

    def __init__(self, storage):
        self.storage = storage

        self.amazon = AmazonConnector(
            use_fixture=True
        )

        self.walmart = WalmartConnector(
            use_fixture=True
        )

        self.bestbuy = BestBuyConnector(
            use_fixture=True
        )

        self.persistence = CompetitivePersistenceService(
            storage=storage
        )

    def get_connectors(self):
        """
        Return all configured competitive source connectors.
        """

        return [
            self.amazon,
            self.walmart,
            self.bestbuy,
        ]

    def fetch_products(
        self,
        query="consumer electronics",
        limit=10,
    ):
        """
        Fetch products from all configured sources.
        """

        results = {}

        for connector in self.get_connectors():
            source = connector.get_source()

            products = connector.fetch_products(
                query=query,
                limit=limit,
            )

            results[source] = products

        return results

    def ingest(
        self,
        canonical_product_id,
        query="consumer electronics",
        limit=10,
    ):
        """
        Run the complete competitive ingestion workflow.

        Amazon is used as the reference product.

        Flow:

            Amazon
                ↓
            canonical product
                ↓
            Walmart + Best Buy matching
                ↓
            ClickHouse storage
        """

        products_by_source = self.fetch_products(
            query=query,
            limit=limit,
        )

        amazon_products = products_by_source.get(
            self.REFERENCE_SOURCE,
            [],
        )

        if not amazon_products:
            return {
                "success": False,
                "reason": "reference_product_not_found",
                "reference_source": self.REFERENCE_SOURCE,
                "canonical_product_id": canonical_product_id,
                "products": products_by_source,
            }

        reference_product = amazon_products[0]

        competitor_products = []

        for source in [
            "WALMART",
            "BESTBUY",
        ]:
            competitor_products.extend(
                products_by_source.get(
                    source,
                    [],
                )
            )

        persistence_result = (
            self.persistence.persist_competitive_product(
                canonical_product_id=canonical_product_id,
                reference_product=reference_product,
                competitor_products=competitor_products,
            )
        )

        return {
            "success": persistence_result.get(
                "success",
                False,
            ),
            "canonical_product_id": canonical_product_id,
            "reference_source": self.REFERENCE_SOURCE,
            "reference_product": reference_product,
            "products_by_source": products_by_source,
            "persistence": persistence_result,
        }