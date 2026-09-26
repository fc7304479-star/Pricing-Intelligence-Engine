from pricing_engine.intelligence.matching_service import (
    ProductMatchingService,
)


class CompetitivePersistenceService:
    """
    Persists matched competitive products using the
    existing ClickHouse storage architecture.

    Flow:
        source products
            ↓
        product_catalog
            ↓
        price_observations
            ↓
        canonical_products
            ↓
        source_product_matches

    Canonical products are persisted idempotently:
        - existing canonical product -> reuse
        - missing canonical product -> create

    Repeated ingestion creates new historical observations
    without creating duplicate canonical identities.
    """

    def __init__(self, storage):
        self.storage = storage
        self.matching_service = ProductMatchingService(
            storage
        )

    def store_source_product(self, product):
        source = str(
            product.get("source") or ""
        ).strip().upper()

        source_product_id = str(
            product.get("source_product_id") or ""
        ).strip()

        if not source:
            raise ValueError(
                "Product source is required"
            )

        if not source_product_id:
            raise ValueError(
                "source_product_id is required"
            )

        data = dict(product)

        data["goods_id"] = source_product_id
        data["source"] = source

        return self.storage.store_normalized(
            data
        )

    def store_source_products(self, products):
        results = []

        for product in products:
            stored = self.store_source_product(
                product
            )

            results.append(
                {
                    "source": product.get(
                        "source",
                        "",
                    ),
                    "source_product_id": product.get(
                        "source_product_id",
                        "",
                    ),
                    "stored": stored,
                }
            )

        return results

    def create_canonical(
        self,
        canonical_product_id,
        reference_product,
    ):
        """
        Reuse an existing canonical product when possible.

        Only create a canonical product when the supplied
        canonical_product_id does not already exist.
        """

        existing = self.storage.get_canonical_product(
            canonical_product_id
        )

        if existing is not None:
            print(
                "[ClickHouse] Canonical product reused | "
                f"id={canonical_product_id}"
            )

            return existing

        created = (
            self.matching_service.create_canonical_from_product(
                product=reference_product,
                canonical_product_id=canonical_product_id,
            )
        )

        if not created:
            return None

        existing = self.storage.get_canonical_product(
            canonical_product_id
        )

        if existing is not None:
            return existing

        return {
            "canonical_product_id": canonical_product_id,
            "canonical_name": (
                reference_product.get(
                    "product_name"
                )
                or "Unnamed Product"
            ),
            "brand": reference_product.get(
                "brand",
                "",
            ),
            "model": reference_product.get(
                "model",
                "",
            ),
            "gtin": reference_product.get(
                "gtin",
                "",
            ),
            "category": reference_product.get(
                "category",
                "consumer_electronics",
            ),
        }

    def link_reference_product(
        self,
        canonical_product_id,
        reference_product,
    ):
        """
        Link the reference product to the canonical product.

        The existing ReplacingMergeTree storage behavior makes
        this operation safe to repeat.
        """

        return self.matching_service.save_match(
            canonical_product_id=canonical_product_id,
            product=reference_product,
            match_method="canonical_seed",
            match_confidence=1.0,
        )

    def link_competitors(
        self,
        competitor_products,
    ):
        """
        Match and link competitor source products.

        Existing matches are safely replaced/updated by the
        existing source-product match storage layer.
        """

        results = []

        for product in competitor_products:
            result = (
                self.matching_service.match_and_link(
                    product
                )
            )

            results.append(
                {
                    "source": product.get(
                        "source",
                        "",
                    ),
                    "source_product_id": product.get(
                        "source_product_id",
                        "",
                    ),
                    **result,
                }
            )

        return results

    def persist_competitive_product(
        self,
        canonical_product_id,
        reference_product,
        competitor_products,
    ):
        """
        Persist one complete competitive product group.

        Important behavior:

        First ingestion:
            source products stored
            canonical product created
            source matches created
            observations stored

        Repeated ingestion:
            source products stored
            existing canonical product reused
            source matches updated/reused
            new price observations stored

        This keeps canonical identity stable while preserving
        price history.
        """

        all_products = [
            reference_product,
            *competitor_products,
        ]

        # -----------------------------------------------------
        # 1. Store source products and price observations
        # -----------------------------------------------------

        storage_results = (
            self.store_source_products(
                all_products
            )
        )

        # -----------------------------------------------------
        # 2. Create OR reuse canonical product
        # -----------------------------------------------------

        canonical_product = self.create_canonical(
            canonical_product_id=canonical_product_id,
            reference_product=reference_product,
        )

        if canonical_product is None:
            return {
                "success": False,
                "reason": (
                    "canonical_product_creation_failed"
                ),
                "storage_results": storage_results,
            }

        canonical_created_or_reused = (
            canonical_product
        )

        # -----------------------------------------------------
        # 3. Link reference product
        # -----------------------------------------------------

        reference_linked = (
            self.link_reference_product(
                canonical_product_id=canonical_product_id,
                reference_product=reference_product,
            )
        )

        # -----------------------------------------------------
        # 4. Match and link competitors
        # -----------------------------------------------------

        competitor_results = (
            self.link_competitors(
                competitor_products
            )
        )

        # -----------------------------------------------------
        # 5. Determine overall success
        # -----------------------------------------------------

        all_competitors_matched = all(
            result.get("matched") is True
            for result in competitor_results
        )

        return {
            "success": all_competitors_matched,
            "canonical_product_id": (
                canonical_product_id
            ),
            "canonical_product": (
                canonical_created_or_reused
            ),
            "storage_results": storage_results,
            "canonical_created_or_reused": True,
            "reference_linked": reference_linked,
            "competitor_results": competitor_results,
        }