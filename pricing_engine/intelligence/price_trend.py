class PriceTrendService:
    """
    Calculates basic price trends from historical
    price observations.

    This service does not persist anything.
    It transforms existing historical observations
    into trend information.
    """

    # =========================================================
    # NORMALIZE PRICE
    # =========================================================

    @staticmethod
    def normalize_price(price):

        if price is None:
            return None

        try:

            price = float(price)

        except (
            TypeError,
            ValueError,
        ):

            return None

        if price < 0:
            return None

        return round(
            price,
            2,
        )

    # =========================================================
    # SORT HISTORY
    # =========================================================

    @staticmethod
    def sort_history(history):

        history = history or []

        return sorted(
            history,
            key=lambda item: str(
                item.get(
                    "observed_at"
                )
                or ""
            ),
        )

    # =========================================================
    # TREND DIRECTION
    # =========================================================

    def calculate_direction(
        self,
        history,
    ):

        history = self.sort_history(
            history
        )

        valid_prices = []

        for item in history:

            price = self.normalize_price(
                item.get("price")
            )

            if price is None:
                continue

            valid_prices.append(
                price
            )

        if len(valid_prices) < 2:

            return "insufficient_data"

        previous_price = valid_prices[
            -2
        ]

        current_price = valid_prices[
            -1
        ]

        if current_price > previous_price:

            return "increasing"

        if current_price < previous_price:

            return "decreasing"

        return "stable"

    # =========================================================
    # SUMMARY
    # =========================================================

    def calculate_summary(
        self,
        history,
    ):

        history = self.sort_history(
            history
        )

        points = []

        for item in history:

            price = self.normalize_price(
                item.get("price")
            )

            if price is None:
                continue

            points.append(
                {
                    "price": price,
                    "observed_at": item.get(
                        "observed_at"
                    ),
                }
            )

        if not points:

            return {
                "trend": "insufficient_data",
                "min_price": None,
                "max_price": None,
                "average_price": None,
                "observation_count": 0,
                "history": [],
            }

        prices = [
            point["price"]
            for point in points
        ]

        return {
            "trend": self.calculate_direction(
                points
            ),

            "min_price": min(
                prices
            ),

            "max_price": max(
                prices
            ),

            "average_price": round(
                sum(prices)
                / len(prices),
                2,
            ),

            "observation_count": len(
                points
            ),

            "history": points,
        }

    # =========================================================
    # ALL COMPETITIVE SOURCES
    # =========================================================

    def calculate_competitive_trends(
        self,
        products,
    ):

        results = []

        for product in products:

            summary = self.calculate_summary(
                product.get(
                    "history",
                    [],
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

                    "match_method": product.get(
                        "match_method"
                    ),

                    "match_confidence": product.get(
                        "match_confidence"
                    ),

                    **summary,
                }
            )

        return results