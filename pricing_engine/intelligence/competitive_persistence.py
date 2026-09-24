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
    """

    def __init__(self, storage):
        self.storage = storage
        self.matching_service = ProductMatchingService(
            storage
        )

    # =========================================================
    # STORE SOURCE PRODUCT
    # =========================================================

    def store_source_product(
        self,
        product,
    ):
        """
        Store a connector product using the existing
        normalized storage pipeline.
        """

        source = str(
            product.get("source") or ""
        ).strip().upper()

        source_product_id = str(
            product.get("source_product_id")
            or ""
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

        # Existing store_normalized() expects goods_id.
        data["goods_id"] = source_product_id

        data["source"] = source

        return self.storage.store_normalized(
            data
        )

    # =========================================================
    # STORE ALL SOURCE PRODUCTS
    # =========================================================

    def store_source_products(
        self,
        products,
    ):
        """
        Store all source products.

        Returns one result per product.
        """

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

    # =========================================================
    # CREATE CANONICAL PRODUCT
    # =========================================================

    def create_canonical(
        self,
        canonical_product_id,
        reference_product,
    ):
        """
        Create the canonical product using the reference
        product as the initial identity seed.
        """

        return (
            self.matching_service
            .create_canonical_from_product(
                product=reference_product,
                canonical_product_id=(
                    canonical_product_id
                ),
            )
        )

    # =========================================================
    # LINK REFERENCE PRODUCT
    # =========================================================

    def link_reference_product(
        self,
        canonical_product_id,
        reference_product,
    ):
        """
        Link the reference product to the canonical product.

        The reference product is the initial canonical seed,
        so it receives canonical_seed as its match method.
        """

        return self.matching_service.save_match(
            canonical_product_id=(
                canonical_product_id
            ),
            product=reference_product,
            match_method="canonical_seed",
            match_confidence=1.0,
        )

    # =========================================================
    # LINK COMPETITORS
    # =========================================================

    def link_competitors(
        self,
        competitor_products,
    ):
        """
        Match and link competitor products against the
        canonical product candidates.
        """

        results = []

        for product in competitor_products:

            result = (
                self.matching_service
                .match_and_link(product)
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

    # =========================================================
    # COMPLETE PERSISTENCE FLOW
    # =========================================================

    def persist_competitive_product(
        self,
        canonical_product_id,
        reference_product,
        competitor_products,
    ):
        """
        Complete persistence flow for one canonical product.

        Steps:

        1. Store reference product.
        2. Store competitor products.
        3. Create canonical product.
        4. Link reference product.
        5. Match and link competitors.
        """

        all_products = [
            reference_product,
            *competitor_products,
        ]

        storage_results = (
            self.store_source_products(
                all_products
            )
        )

        canonical_created = self.create_canonical(
            canonical_product_id=(
                canonical_product_id
            ),
            reference_product=reference_product,
        )

        if not canonical_created:
            return {
                "success": False,
                "reason": (
                    "canonical_product_creation_failed"
                ),
                "storage_results": storage_results,
            }

        reference_linked = (
            self.link_reference_product(
                canonical_product_id=(
                    canonical_product_id
                ),
                reference_product=reference_product,
            )
        )

        competitor_results = (
            self.link_competitors(
                competitor_products
            )
        )

        all_competitors_matched = all(
            result.get("matched") is True
            for result in competitor_results
        )

        return {
            "success": all_competitors_matched,
            "canonical_product_id": (
                canonical_product_id
            ),
            "storage_results": storage_results,
            "canonical_created": canonical_created,
            "reference_linked": reference_linked,
            "competitor_results": competitor_results,
        }