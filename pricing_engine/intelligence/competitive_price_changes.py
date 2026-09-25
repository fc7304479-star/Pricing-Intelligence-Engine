from pricing_engine.intelligence.product_normalizer import (
    ProductNormalizer,
)


class CompetitivePriceChangeService:
    """
    Calculates price changes for matched competitive products.

    Input:
        source-wise historical observations

    Output:
        previous price
        current price
        change amount
        change percent
        direction
    """

    def __init__(self):
        self.normalizer = ProductNormalizer()

    # =========================================================
    # CALCULATE ONE PRICE CHANGE
    # =========================================================

    def calculate_change(
        self,
        previous_price,
        current_price,
    ):

        if (
            previous_price is None
            or current_price is None
        ):
            return {
                "previous_price": previous_price,
                "current_price": current_price,
                "change_amount": None,
                "change_percent": None,
                "direction": "unknown",
            }

        try:

            previous_price = float(
                previous_price
            )

            current_price = float(
                current_price
            )

        except (
            TypeError,
            ValueError,
        ):

            return {
                "previous_price": previous_price,
                "current_price": current_price,
                "change_amount": None,
                "change_percent": None,
                "direction": "unknown",
            }

        change_amount = (
            current_price
            - previous_price
        )

        change_percent = None

        if previous_price != 0:

            change_percent = (
                change_amount
                / previous_price
            ) * 100

            change_percent = round(
                change_percent,
                2,
            )

        change_amount = round(
            change_amount,
            2,
        )

        if change_amount > 0:

            direction = "increased"

        elif change_amount < 0:

            direction = "decreased"

        else:

            direction = "unchanged"

        return {
            "previous_price": previous_price,
            "current_price": current_price,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "direction": direction,
        }

    # =========================================================
    # CALCULATE SOURCE HISTORY CHANGE
    # =========================================================

    def calculate_history_change(
        self,
        history,
    ):

        if not history:

            return {
                "has_change": False,
                "previous": None,
                "current": None,
                "change": None,
            }

        sorted_history = sorted(
            history,
            key=lambda item: str(
                item.get("observed_at")
                or ""
            ),
        )

        if len(sorted_history) < 2:

            current = sorted_history[-1]

            return {
                "has_change": False,
                "previous": None,
                "current": {
                    "price": current.get(
                        "price"
                    ),
                    "observed_at": current.get(
                        "observed_at"
                    ),
                },
                "change": None,
            }

        previous = sorted_history[-2]
        current = sorted_history[-1]

        change = self.calculate_change(
            previous_price=previous.get(
                "price"
            ),
            current_price=current.get(
                "price"
            ),
        )

        return {
            "has_change": (
                change["direction"]
                != "unchanged"
            ),
            "previous": {
                "price": previous.get(
                    "price"
                ),
                "observed_at": previous.get(
                    "observed_at"
                ),
            },
            "current": {
                "price": current.get(
                    "price"
                ),
                "observed_at": current.get(
                    "observed_at"
                ),
            },
            "change": change,
        }

    # =========================================================
    # CALCULATE ALL SOURCES
    # =========================================================

    def calculate_competitive_changes(
        self,
        products,
    ):

        results = []

        for product in products:

            history = product.get(
                "history",
                [],
            )

            change_result = (
                self.calculate_history_change(
                    history
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
                    **change_result,
                }
            )

        return results

    # =========================================================
    # ONLY ACTUAL CHANGES
    # =========================================================

    def get_actual_changes(
        self,
        products,
    ):

        results = (
            self.calculate_competitive_changes(
                products
            )
        )

        return [
            result
            for result in results
            if result.get("has_change") is True
        ]