from pricing_engine.intelligence.llm_selector import LLMSelector


class PriceExtractor:

    PRICE_SELECTORS = [

        ".product-price .price-value",

        ".product-price span",

        '[itemprop="price"]',

        ".price",

        ".sale-price",

        ".our-price",

        ".current-price",

        ".product__price",

        ".price-final",

    ]

    def __init__(self):

        self.llm = LLMSelector()

    async def extract(self, page):

        # ---------------------------------
        # First Try Normal Selectors
        # ---------------------------------

        for selector in self.PRICE_SELECTORS:

            try:

                locator = page.locator(selector)

                if await locator.count() == 0:
                    continue

                text = (
                    await locator.first.inner_text()
                ).strip()

                if text:

                    print(
                        f"[CSS] Price Found -> {selector}"
                    )

                    return text

            except Exception:

                continue

        print(
            "[CSS] No selector worked."
        )

        # ---------------------------------
        # LLM Fallback
        # ---------------------------------

        try:

            html = await page.content()

            selector = self.llm.find_price_selector(html)

            if selector:

                locator = page.locator(selector)

                if await locator.count() > 0:

                    text = (
                        await locator.first.inner_text()
                    ).strip()

                    if text:

                        print(
                            f"[LLM] Price Found -> {selector}"
                        )

                        return text

        except Exception as e:

            print(
                f"[LLM ERROR] {e}"
            )

        return ""