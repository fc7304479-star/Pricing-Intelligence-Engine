class StockDetector:

    STOCK_SELECTORS = [

        ".stock",

        ".availability",

        "#stock",

        ".inventory",

        ".product-stock"

    ]

    OUT_OF_STOCK = [

        "out of stock",

        "sold out",

        "unavailable",

        "currently unavailable"

    ]

    async def detect(self, page):

        for selector in self.STOCK_SELECTORS:

            try:

                locator = page.locator(selector)

                if await locator.count():

                    text = (
                        await locator.first.inner_text()
                    ).lower()

                    for keyword in self.OUT_OF_STOCK:

                        if keyword in text:

                            return False

                    return True

            except Exception:
                pass

        return None