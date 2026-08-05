from pricing_engine.intelligence.price_extractor import PriceExtractor
from pricing_engine.intelligence.llm_selector import LLMSelector
from pricing_engine.intelligence.html_cleaner import HTMLCleaner
from pricing_engine.intelligence.selector_cache import SelectorCache


class ProductParser:

    def __init__(self):

        self.price_extractor = PriceExtractor()

        self.llm = LLMSelector()

        self.cleaner = HTMLCleaner()

        self.cache = SelectorCache()

    async def parse(self, page):

        title = await page.title()

        try:

            price = await self.price_extractor.extract(page)

        except Exception:

            html = await page.content()

            html = self.cleaner.clean(html)

            new_selector = self.llm.suggest(

                html,

                ".product-price",

            )

            self.cache.save(

                ".product-price",

                new_selector,

            )

            print(

                "[AI] Recovered selector ->",

                new_selector,

            )

            price = "Unknown"

        return {

            "title": title,

            "url": page.url,

            "price": price,

        }