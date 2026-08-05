import re


class PriceParser:
    """
    Converts price string into structured data.
    """

    @staticmethod
    def parse(price_text: str):

        if not price_text:
            return {
                "currency": "",
                "price": None
            }

        currency = ""

        if "$" in price_text:
            currency = "USD"

        match = re.search(r"(\d+(?:\.\d+)?)", price_text)

        if match:
            value = float(match.group(1))
        else:
            value = None

        return {
            "currency": currency,
            "price": value
        }