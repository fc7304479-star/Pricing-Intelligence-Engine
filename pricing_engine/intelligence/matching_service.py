from pricing_engine.intelligence.product_matcher import ProductMatcher
from pricing_engine.intelligence.product_normalizer import ProductNormalizer


class ProductMatchingService:
    """
    Coordinates product normalization, candidate discovery,
    product matching, and persistence.
    """

    def __init__(self, storage):
        self.storage = storage
        self.normalizer = ProductNormalizer()
        self.matcher = ProductMatcher()

    # =========================================================
    # CREATE CANONICAL PRODUCT FROM SOURCE PRODUCT
    # =========================================================

    def create_canonical_from_product(
        self,
        product,
        canonical_product_id,
    ):
        """
        Create a canonical product using identity information
        from a source product.
        """

        normalized = self.normalizer.normalize_product(product)

        canonical_name = (
            product.get("product_name")
            or normalized["product_name"]
            or "Unnamed Product"
        )

        return self.storage.create_canonical_product(
            canonical_product_id=canonical_product_id,
            canonical_name=canonical_name,
            brand=product.get("brand") or "",
            model=product.get("model") or "",
            gtin=product.get("gtin") or "",
            category=product.get(
                "category",
                "consumer_electronics",
            ),
        )

    # =========================================================
    # SAVE SOURCE PRODUCT MATCH
    # =========================================================

    def save_match(
        self,
        canonical_product_id,
        product,
        match_method,
        match_confidence,
    ):
        """
        Save the relationship between a source product
        and a canonical product.
        """

        normalized = self.normalizer.normalize_product(product)

        source = normalized["source"]
        source_product_id = normalized["source_product_id"]

        if not source:
            raise ValueError(
                "Source product is missing source"
            )

        if not source_product_id:
            raise ValueError(
                "Source product is missing source_product_id"
            )

        return self.storage.save_source_product_match(
            canonical_product_id=canonical_product_id,
            source=source,
            source_product_id=source_product_id,
            match_method=match_method,
            match_confidence=match_confidence,
        )

    # =========================================================
    # MATCH TWO PRODUCTS
    # =========================================================

    def compare_products(
        self,
        product_a,
        product_b,
    ):
        """
        Compare two source products using ProductMatcher.
        """

        return self.matcher.match(
            product_a,
            product_b,
        )

    # =========================================================
    # FIND CANDIDATE CANONICAL PRODUCTS
    # =========================================================

    def find_candidates(
        self,
        product,
    ):
        """
        Find possible canonical products for a source product.

        Candidate discovery order:

        1. GTIN
        2. Brand + Model
        3. Model

        Candidates are deduplicated by canonical_product_id.
        """

        normalized = self.normalizer.normalize_product(product)

        candidates = {}

        # -----------------------------------------------------
        # 1. GTIN
        # -----------------------------------------------------

        gtin = normalized["normalized_gtin"]

        if gtin:
            gtin_candidates = (
                self.storage.find_canonical_products_by_gtin(
                    gtin
                )
            )

            for candidate in gtin_candidates:
                candidate_id = candidate[
                    "canonical_product_id"
                ]

                candidates[candidate_id] = candidate

        # -----------------------------------------------------
        # 2. BRAND + MODEL
        # -----------------------------------------------------

        brand = normalized["normalized_brand"]
        model = normalized["normalized_model"]

        if brand and model:
            brand_model_candidates = (
                self.storage.find_canonical_products_by_brand_model(
                    brand,
                    model,
                )
            )

            for candidate in brand_model_candidates:
                candidate_id = candidate[
                    "canonical_product_id"
                ]

                candidates[candidate_id] = candidate

        # -----------------------------------------------------
        # 3. MODEL
        # -----------------------------------------------------

        if model:
            model_candidates = (
                self.storage.find_canonical_products_by_model(
                    model
                )
            )

            for candidate in model_candidates:
                candidate_id = candidate[
                    "canonical_product_id"
                ]

                candidates[candidate_id] = candidate

        return list(candidates.values())

    # =========================================================
    # MATCH PRODUCT AGAINST CANDIDATES
    # =========================================================

    def match_against_candidates(
        self,
        product,
    ):
        """
        Find canonical candidates and evaluate each candidate
        using ProductMatcher.

        This method does NOT save matches.
        """

        candidates = self.find_candidates(product)

        results = []

        for candidate in candidates:
            result = self.match_to_canonical(
                product,
                candidate,
            )

            results.append(
                {
                    "canonical_product": candidate,
                    "matched": result["matched"],
                    "match_method": result["match_method"],
                    "match_confidence": result[
                        "match_confidence"
                    ],
                }
            )

        return results

    # =========================================================
    # FIND BEST MATCH
    # =========================================================

    def find_best_match(
        self,
        product,
    ):
        """
        Find the highest-confidence canonical match.

        Returns None when no confirmed match exists.
        """

        results = self.match_against_candidates(product)

        matched_results = [
            result
            for result in results
            if result["matched"]
        ]

        if not matched_results:
            return None

        matched_results.sort(
            key=lambda result: (
                result["match_confidence"],
                result["canonical_product"][
                    "canonical_product_id"
                ],
            ),
            reverse=True,
        )

        return matched_results[0]

    # =========================================================
    # CREATE + LINK NEW CANONICAL PRODUCT
    # =========================================================

    def create_and_link(
        self,
        product,
        canonical_product_id,
        match_method="canonical_seed",
        match_confidence=1.0,
    ):
        """
        Create a canonical product and immediately link
        the source product to it.
        """

        created = self.create_canonical_from_product(
            product=product,
            canonical_product_id=canonical_product_id,
        )

        if not created:
            return {
                "success": False,
                "reason": "canonical_product_creation_failed",
            }

        self.save_match(
            canonical_product_id=canonical_product_id,
            product=product,
            match_method=match_method,
            match_confidence=match_confidence,
        )

        return {
            "success": True,
            "canonical_product_id": canonical_product_id,
            "match_method": match_method,
            "match_confidence": match_confidence,
        }

    # =========================================================
    # MATCH AGAINST EXISTING CANONICAL PRODUCT
    # =========================================================

    def match_to_canonical(
        self,
        product,
        canonical_product,
    ):
        """
        Compare a source product against a canonical product.
        """

        canonical_as_product = {
            "source": "CANONICAL",
            "source_product_id": canonical_product.get(
                "canonical_product_id",
                "",
            ),
            "product_name": canonical_product.get(
                "canonical_name",
                "",
            ),
            "brand": canonical_product.get(
                "brand",
                "",
            ),
            "model": canonical_product.get(
                "model",
                "",
            ),
            "gtin": canonical_product.get(
                "gtin",
                "",
            ),
        }

        return self.matcher.match(
            product,
            canonical_as_product,
        )

    # =========================================================
    # MATCH AND LINK PRODUCT TO EXISTING CANONICAL
    # =========================================================

    def match_and_link(
        self,
        product,
    ):
        """
        Find the best canonical match for a source product.

        If a confirmed match exists, save the relationship.

        If no match exists, nothing is created.
        """

        best_match = self.find_best_match(product)

        if best_match is None:
            return {
                "matched": False,
                "reason": "no_match",
            }

        canonical_product = best_match[
            "canonical_product"
        ]

        canonical_product_id = canonical_product[
            "canonical_product_id"
        ]

        match_method = best_match[
            "match_method"
        ]

        match_confidence = best_match[
            "match_confidence"
        ]

        saved = self.save_match(
            canonical_product_id=canonical_product_id,
            product=product,
            match_method=match_method,
            match_confidence=match_confidence,
        )

        if not saved:
            return {
                "matched": False,
                "reason": "match_persistence_failed",
                "canonical_product_id": canonical_product_id,
                "match_method": match_method,
                "match_confidence": match_confidence,
            }

        return {
            "matched": True,
            "canonical_product_id": canonical_product_id,
            "match_method": match_method,
            "match_confidence": match_confidence,
        }

    # =========================================================
    # GET CANONICAL MATCHES
    # =========================================================

    def get_matches(
        self,
        canonical_product_id,
    ):
        """
        Return all source products linked to a canonical product.
        """

        return self.storage.get_product_matches(
            canonical_product_id
        )