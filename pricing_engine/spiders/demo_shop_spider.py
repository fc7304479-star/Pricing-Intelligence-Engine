import json
import random
from datetime import datetime

import scrapy

from pricing_engine.browser.interceptor import NetworkInterceptor
from pricing_engine.browser.navigator import BrowserNavigator
from pricing_engine.browser.fingerprint import Fingerprint
from pricing_engine.browser.proxy_manager import ProxyManager
from pricing_engine.intelligence.parser import ProductParser
from pricing_engine.queue.redis_queue import RedisQueue


class DemoShopSpider(scrapy.Spider):

    name = "demo_shop"

    allowed_domains = [
        "demowebshop.tricentis.com"
    ]

    start_urls = [
        "https://demowebshop.tricentis.com/"
    ]

    async def start(self):

        fp = Fingerprint()

        for url in self.start_urls:

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_close_page,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "default",

                    # Random Fingerprint
                    "playwright_context_kwargs": {

                        "user_agent": fp.random_user_agent(),

                        "viewport": fp.random_viewport(),

                        "locale": fp.random_locale(),

                        "timezone_id": fp.random_timezone(),

                    },
                },
            )

    async def parse(self, response):

        page = response.meta["playwright_page"]

        navigator = BrowserNavigator(page)

        interceptor = NetworkInterceptor()
        await interceptor.attach(page)

        queue = RedisQueue()

        proxy = ProxyManager()

        self.logger.info("=" * 70)

        self.logger.info(
            f"TITLE : {await page.title()}"
        )

        self.logger.info(
            f"URL : {page.url}"
        )

        self.logger.info(
            f"USER AGENT : {await page.evaluate('navigator.userAgent')}"
        )

        # -------------------------------
        # Human Behaviour
        # -------------------------------

        await page.wait_for_timeout(
            random.randint(1000, 2500)
        )

        await page.mouse.move(
            random.randint(200, 800),
            random.randint(150, 500),
            steps=25,
        )

        await page.mouse.wheel(0, 600)

        await page.wait_for_timeout(
            random.randint(800, 1800)
        )

        await page.mouse.wheel(0, -400)

        products = page.locator(".product-item")

        count = await products.count()

        self.logger.info(
            f"TOTAL PRODUCTS : {count}"
        )

        for i in range(count):

            name = await products.nth(i).locator(
                ".product-title"
            ).inner_text()

            print(name)

        first_product = products.nth(0)

        href = await first_product.locator(
            ".product-title a"
        ).get_attribute("href")

        product_url = response.urljoin(href)

        self.logger.info(
            f"PRODUCT URL : {product_url}"
        )

        await navigator.goto(product_url)

        await page.wait_for_timeout(2000)

        self.logger.info(
            f"NOW AT : {page.url}"
        )

        # -------------------------------
        # Gift Card Form
        # -------------------------------

        await page.fill(
            "#giftcard_2_RecipientName",
            "John"
        )

        await page.fill(
            "#giftcard_2_RecipientEmail",
            "john@example.com"
        )

        await page.fill(
            "#giftcard_2_SenderName",
            "AI Bot"
        )

        await page.fill(
            "#giftcard_2_SenderEmail",
            "bot@example.com"
        )

        await page.fill(
            "#giftcard_2_Message",
            "Pricing Intelligence Engine"
        )

        self.logger.info(
            "Gift Card Form Filled"
        )

        await page.wait_for_timeout(
            random.randint(1000, 2000)
        )

        await page.click(
            "#add-to-cart-button-2"
        )

        self.logger.info(
            "Clicked Add To Cart"
        )

        await page.wait_for_timeout(5000)

        # -------------------------------
        # Parse Product
        # -------------------------------

        parser = ProductParser()

        product = await parser.parse(page)

        network = interceptor.get_responses()

        self.logger.info(
            f"PRICE : {product['price']}"
        )

        self.logger.info(
            f"JSON RESPONSES : {len(network)}"
        )

        product["network"] = network

        product["timestamp"] = (
            datetime.utcnow().isoformat()
        )

        product["source"] = "Demo Web Shop"

        product["currency"] = "USD"

        product["proxy"] = proxy.get_proxy()

        try:

            queue.push(
                json.dumps(product)
            )

            self.logger.info(
                "Product pushed to Redis Queue."
            )

        except Exception as e:

            self.logger.warning(
                f"Redis Error : {e}"
            )

        yield product

        await page.close()

    async def errback_close_page(self, failure):

        page = failure.request.meta.get(
            "playwright_page"
        )

        if page:

            await page.close()

        self.logger.error(repr(failure))