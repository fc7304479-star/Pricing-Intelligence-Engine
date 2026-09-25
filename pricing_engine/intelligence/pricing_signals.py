class PricingSignalService:
    """
    Generates simple, explainable, rule-based pricing signals.

    This service does not persist data.
    It converts competitive pricing and price-trend
    information into business-readable signals.
    """

    REFERENCE_SOURCE = "AMAZON"

    # =========================================================
    # SOURCE DISPLAY NAME
    # =========================================================

    @staticmethod
    def display_source(source):
        source = str(source or "").strip().upper()

        source_names = {
            "AMAZON": "Amazon",
            "WALMART": "Walmart",
            "BESTBUY": "Best Buy",
        }

        return source_names.get(
            source,
            source.title(),
        )

    # =========================================================
    # SAFE NUMBER CONVERSION
    # =========================================================

    @staticmethod
    def to_float(value):

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # =========================================================
    # PRICE CHANGE SIGNAL
    # =========================================================

    def generate_price_change_signal(
        self,
        product,
    ):

        source = str(
            product.get("source")
            or ""
        ).strip().upper()

        if not source:
            return None

        change = product.get("change") or {}

        direction = str(
            change.get("direction")
            or ""
        ).strip().lower()

        change_percent = self.to_float(
            change.get("change_percent")
        )

        change_amount = self.to_float(
            change.get("change_amount")
        )

        display_name = self.display_source(
            source
        )

        if direction == "decreased":

            percent_text = (
                f"{abs(change_percent):.2f}%"
                if change_percent is not None
                else "an unknown percentage"
            )

            return {
                "signal_type": (
                    "COMPETITOR_PRICE_DECREASE"
                ),
                "severity": "medium",
                "source": source,
                "message": (
                    f"{display_name} reduced price by "
                    f"{percent_text}."
                ),
                "change_percent": change_percent,
                "change_amount": change_amount,
            }

        if direction == "increased":

            percent_text = (
                f"{abs(change_percent):.2f}%"
                if change_percent is not None
                else "an unknown percentage"
            )

            return {
                "signal_type": (
                    "COMPETITOR_PRICE_INCREASE"
                ),
                "severity": "low",
                "source": source,
                "message": (
                    f"{display_name} increased price by "
                    f"{percent_text}."
                ),
                "change_percent": change_percent,
                "change_amount": change_amount,
            }

        return None

    # =========================================================
    # REFERENCE VS MARKET SIGNAL
    # =========================================================

    def generate_market_signal(
        self,
        reference_price,
        market_average,
    ):

        reference_price = self.to_float(
            reference_price
        )

        market_average = self.to_float(
            market_average
        )

        if (
            reference_price is None
            or market_average is None
            or market_average == 0
        ):
            return None

        difference_percent = (
            (
                reference_price
                - market_average
            )
            / market_average
        ) * 100

        difference_percent = round(
            difference_percent,
            2,
        )

        if difference_percent > 0:

            return {
                "signal_type": (
                    "REFERENCE_ABOVE_MARKET"
                ),
                "severity": "high",
                "source": self.REFERENCE_SOURCE,
                "message": (
                    "Reference price is "
                    f"{difference_percent:.2f}% "
                    "above market average."
                ),
                "difference_percent": (
                    difference_percent
                ),
            }

        if difference_percent < 0:

            return {
                "signal_type": (
                    "REFERENCE_BELOW_MARKET"
                ),
                "severity": "low",
                "source": self.REFERENCE_SOURCE,
                "message": (
                    "Reference price is "
                    f"{abs(difference_percent):.2f}% "
                    "below market average."
                ),
                "difference_percent": (
                    difference_percent
                ),
            }

        return None

    # =========================================================
    # REVIEW PRICING SIGNAL
    # =========================================================

    def generate_review_signal(
        self,
        reference_price,
        market_average,
    ):

        reference_price = self.to_float(
            reference_price
        )

        market_average = self.to_float(
            market_average
        )

        if (
            reference_price is None
            or market_average is None
            or market_average == 0
        ):
            return None

        difference_percent = (
            (
                reference_price
                - market_average
            )
            / market_average
        ) * 100

        difference_percent = round(
            difference_percent,
            2,
        )

        if difference_percent >= 5:

            return {
                "signal_type": "REVIEW_PRICING",
                "severity": "high",
                "source": self.REFERENCE_SOURCE,
                "message": (
                    "Review pricing for this "
                    "product."
                ),
                "difference_percent": (
                    difference_percent
                ),
            }

        return None

    # =========================================================
    # ALL SIGNALS FOR ONE PRODUCT
    # =========================================================

    def generate_signals(
        self,
        reference_price,
        market_average,
        price_changes,
    ):

        signals = []

        # -----------------------------------------------------
        # Reference vs market
        # -----------------------------------------------------

        market_signal = (
            self.generate_market_signal(
                reference_price=reference_price,
                market_average=market_average,
            )
        )

        if market_signal is not None:

            signals.append(
                market_signal
            )

        # -----------------------------------------------------
        # Review pricing
        # -----------------------------------------------------

        review_signal = (
            self.generate_review_signal(
                reference_price=reference_price,
                market_average=market_average,
            )
        )

        if review_signal is not None:

            signals.append(
                review_signal
            )

        # -----------------------------------------------------
        # Competitor price changes
        # -----------------------------------------------------

        for product in (
            price_changes or []
        ):

            source = str(
                product.get("source")
                or ""
            ).strip().upper()

            if source == self.REFERENCE_SOURCE:
                continue

            signal = (
                self.generate_price_change_signal(
                    product
                )
            )

            if signal is not None:

                signals.append(
                    signal
                )

        return signals

    # =========================================================
    # COMPLETE COMPETITIVE SIGNAL SUMMARY
    # =========================================================

    def analyze(
        self,
        reference_price,
        market_average,
        price_changes,
    ):

        signals = self.generate_signals(
            reference_price=reference_price,
            market_average=market_average,
            price_changes=price_changes,
        )

        return {
            "reference_source": (
                self.REFERENCE_SOURCE
            ),
            "reference_price": (
                self.to_float(
                    reference_price
                )
            ),
            "market_average": (
                self.to_float(
                    market_average
                )
            ),
            "signal_count": len(
                signals
            ),
            "signals": signals,
        }