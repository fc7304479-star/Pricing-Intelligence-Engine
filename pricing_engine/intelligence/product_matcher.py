from pricing_engine.intelligence.product_normalizer import ProductNormalizer


class ProductMatcher:
    """
    Conservative product identity matcher.

    Matching priority:
        1. GTIN exact
        2. Model + brand exact
        3. Model exact
        4. No match

    The matcher never forces an uncertain match.
    """

    GTIN_CONFIDENCE = 1.00
    BRAND_MODEL_CONFIDENCE = 0.98
    MODEL_CONFIDENCE = 0.95

    def __init__(self):
        self.normalizer = ProductNormalizer()

    def match(self, product_a, product_b):
        """
        Compare two product dictionaries.

        Returns:
            {
                "matched": bool,
                "match_method": str,
                "match_confidence": float
            }
        """

        a = self.normalizer.normalize_product(
            product_a
        )

        b = self.normalizer.normalize_product(
            product_b
        )

        # -----------------------------------------------------
        # 1. GTIN EXACT MATCH
        # -----------------------------------------------------

        gtin_a = a["normalized_gtin"]
        gtin_b = b["normalized_gtin"]

        if gtin_a and gtin_b:

            if gtin_a == gtin_b:

                return {
                    "matched": True,
                    "match_method": "gtin_exact",
                    "match_confidence": self.GTIN_CONFIDENCE,
                }

            # Both products have GTINs but they differ.
            # Do not allow weaker matching to override this.
            return {
                "matched": False,
                "match_method": "gtin_conflict",
                "match_confidence": 0.0,
            }

        # -----------------------------------------------------
        # 2. BRAND + MODEL EXACT MATCH
        # -----------------------------------------------------

        brand_a = a["normalized_brand"]
        brand_b = b["normalized_brand"]

        model_a = a["normalized_model"]
        model_b = b["normalized_model"]

        if (
            brand_a
            and brand_b
            and model_a
            and model_b
        ):

            if (
                brand_a == brand_b
                and model_a == model_b
            ):

                return {
                    "matched": True,
                    "match_method": "brand_model_exact",
                    "match_confidence": self.BRAND_MODEL_CONFIDENCE,
                }

        # -----------------------------------------------------
        # 3. MODEL EXACT MATCH
        # -----------------------------------------------------

        if (
            model_a
            and model_b
            and model_a == model_b
        ):

            return {
                "matched": True,
                "match_method": "model_exact",
                "match_confidence": self.MODEL_CONFIDENCE,
            }

        # -----------------------------------------------------
        # 4. NO MATCH
        # -----------------------------------------------------

        return {
            "matched": False,
            "match_method": "no_match",
            "match_confidence": 0.0,
        }