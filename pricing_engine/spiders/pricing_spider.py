import scrapy

from pricing_engine.browser.manager import BrowserManager
from pricing_engine.browser.actions import BrowserActions
from pricing_engine.browser.interceptor import NetworkInterceptor
from pricing_engine.extractors.product_extractor import ProductExtractor


class PricingSpider(scrapy.Spider):

    name = "pricing"

    allowed_domains = [
        "coffee-cart.app"
    ]

    start_urls = [
        "https://coffee-cart.app"
    ]

    async def start(self):

        for url in self.start_urls:

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                errback=self.errback_close_page,
            )

    async def parse(self, response):

        page = response.meta["playwright_page"]

        browser_manager = BrowserManager()
        await browser_manager.attach(page)

        interceptor = NetworkInterceptor()
        await interceptor.attach(page)

        actions = BrowserActions(page)

        self.logger.info(f"STATUS: {response.status}")
        self.logger.info(f"URL: {response.url}")

        await actions.wait_network()

        title = await actions.get_title()

        self.logger.info(f"TITLE: {title}")

        extractor = ProductExtractor(page)

        products = await extractor.extract()

        self.logger.info(
            f"PRODUCTS FOUND: {len(products)}"
        )

        # -----------------------
        # Add product
        # -----------------------

        await actions.click_product("Espresso")

        self.logger.info("Espresso Added")

        # -----------------------
        # Open cart
        # -----------------------

        await actions.open_cart()

        self.logger.info("Cart Opened")

        # Give XHR time to finish
        await page.wait_for_timeout(2000)

        yield {

            "title": title,

            "url": response.url,

            "products": products,

            "network": interceptor.get_json_responses()

        }

        # Close page
        await page.close()

    async def errback_close_page(self, failure):

        page = failure.request.meta.get(
            "playwright_page"
        )

        if page:
            await page.close()

        self.logger.error(repr(failure))