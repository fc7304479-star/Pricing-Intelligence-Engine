from pricing_engine.intelligence.product_matcher import (
    ProductMatcher,
)
from pricing_engine.intelligence.price_comparison import (
    PriceComparisonService,
)


class CompetitivePricingService:
    """
    Combines product matching and competitive price comparison.

    This service works in memory first and does not persist
    anything to ClickHouse.
    """

    def __init__(
        self,
        reference_source="AMAZON",
    ):
        self.reference_source = (
            str(reference_source)
            .strip()
            .upper()
        )

        self.matcher = ProductMatcher()

        self.price_comparison = (
            PriceComparisonService(
                reference_source=self.reference_source
            )
        )

    # =========================================================
    # MATCH PRODUCTS
    # =========================================================

    def match_products(
        self,
        reference_product,
        competitor_products,
    ):
        """
        Compare each competitor product against the
        reference product.

        Only confirmed matches are returned.
        """

        matched_products = [
            reference_product
        ]

        match_results = []

        for competitor in competitor_products:

            result = self.matcher.match(
                reference_product,
                competitor,
            )

            match_results.append(
                {
                    "source": competitor.get(
                        "source",
                        "",
                    ),
                    "source_product_id": competitor.get(
                        "source_product_id",
                        "",
                    ),
                    "matched": result["matched"],
                    "match_method": result[
                        "match_method"
                    ],
                    "match_confidence": result[
                        "match_confidence"
                    ],
                }
            )

            if result["matched"]:
                matched_products.append(
                    competitor
                )

        return {
            "matched_products": matched_products,
            "match_results": match_results,
        }

    # =========================================================
    # BUILD COMPETITIVE COMPARISON
    # =========================================================

    def compare(
        self,
        reference_product,
        competitor_products,
    ):
        """
        Match competitors against the reference product
        and calculate competitive pricing metrics.

        Unmatched competitors are excluded from the
        market-average calculation.
        """

        matching = self.match_products(
            reference_product=reference_product,
            competitor_products=competitor_products,
        )

        matched_products = matching[
            "matched_products"
        ]

        comparison = (
            self.price_comparison.compare_products(
                matched_products
            )
        )

        return {
            "reference_source": (
                self.reference_source
            ),
            "reference_product": (
                comparison["reference_product"]
            ),
            "market_average": (
                comparison["market_average"]
            ),
            "products": (
                comparison["products"]
            ),
            "match_results": (
                matching["match_results"]
            ),
        }