class PriceComparisonService:
    """
    Calculates competitive pricing metrics for products
    that have already been matched across sources.
    """

    def __init__(self, reference_source="AMAZON"):
        self.reference_source = (
            str(reference_source)
            .strip()
            .upper()
        )

    # =========================================================
    # MARKET AVERAGE
    # =========================================================

    def calculate_market_average(
        self,
        products,
    ):
        """
        Calculate the average current price across
        products that have a valid numeric price.
        """

        prices = []

        for product in products:
            price = product.get("price")

            if price is None:
                continue

            try:
                price = float(price)
            except (
                TypeError,
                ValueError,
            ):
                continue

            if price < 0:
                continue

            prices.append(price)

        if not prices:
            return None

        return round(
            sum(prices) / len(prices),
            2,
        )

    # =========================================================
    # PRICE DIFFERENCE PERCENT
    # =========================================================

    def calculate_difference_percent(
        self,
        price,
        market_average,
    ):
        """
        Calculate percentage difference from market average.

        Formula:

            ((price - market_average) / market_average) * 100
        """

        if price is None:
            return None

        if market_average is None:
            return None

        try:
            price = float(price)
            market_average = float(market_average)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if market_average == 0:
            return None

        difference = (
            (price - market_average)
            / market_average
        ) * 100

        return round(
            difference,
            2,
        )

    # =========================================================
    # BUILD COMPARISON
    # =========================================================

    def compare_products(
        self,
        products,
    ):
        """
        Build a competitive pricing comparison.

        The input should contain products already confirmed
        as the same canonical product.
        """

        if not products:
            return {
                "reference_source": self.reference_source,
                "market_average": None,
                "products": [],
            }

        market_average = (
            self.calculate_market_average(
                products
            )
        )

        comparison_products = []

        for product in products:
            price = product.get("price")

            difference_percent = (
                self.calculate_difference_percent(
                    price,
                    market_average,
                )
            )

            comparison_products.append(
                {
                    "source": product.get(
                        "source",
                        "",
                    ),
                    "source_product_id": product.get(
                        "source_product_id",
                        "",
                    ),
                    "product_name": product.get(
                        "product_name",
                        "",
                    ),
                    "price": price,
                    "currency": product.get(
                        "currency",
                        "USD",
                    ),
                    "availability": product.get(
                        "availability",
                        "unknown",
                    ),
                    "price_difference_percent": (
                        difference_percent
                    ),
                }
            )

        reference_product = None

        for product in comparison_products:
            if (
                str(
                    product["source"]
                ).upper()
                == self.reference_source
            ):
                reference_product = product
                break

        return {
            "reference_source": self.reference_source,
            "reference_product": reference_product,
            "market_average": market_average,
            "products": comparison_products,
        }