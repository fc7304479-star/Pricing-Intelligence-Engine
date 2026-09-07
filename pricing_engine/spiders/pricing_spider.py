import random
import re
from datetime import datetime, timezone

import scrapy

from pricing_engine.browser.interceptor import NetworkInterceptor
from pricing_engine.extractors.product_extractor import ProductExtractor


class PricingSpider(scrapy.Spider):

    name = "pricing"

    allowed_domains = [
        "us.shein.com",
    ]

    start_urls = [
        "https://us.shein.com/",
    ]

    # =========================================================
    # PLAYWRIGHT PAGE INIT
    # =========================================================
    #
    # This runs BEFORE scrapy-playwright navigates
    # the page to SHEIN.
    #
    # Therefore we can capture the initial XHR/FETCH
    # requests generated during page loading.
    #
    # =========================================================

    async def playwright_page_init(
        self,
        page,
        request
    ):

        interceptor = NetworkInterceptor()

        await interceptor.attach(
            page
        )

        # Keep the SAME interceptor reference on the page.
        page._pricing_interceptor = interceptor

        self.logger.info(
            "[NETWORK] Interceptor attached BEFORE navigation"
        )

    # =========================================================
    # START
    # =========================================================

    async def start(self):

        for url in self.start_urls:

            yield scrapy.Request(

                url=url,

                callback=self.parse,

                errback=self.errback_close_page,

                meta={

                    "playwright": True,

                    "playwright_include_page": True,

                    "playwright_context": "default",

                    # -------------------------------------------------
                    # IMPORTANT
                    # -------------------------------------------------
                    #
                    # Attach interceptor BEFORE page.goto()
                    #
                    "playwright_page_init_callback": (
                        self.playwright_page_init
                    ),
                },
            )

    # =========================================================
    # PARSE
    # =========================================================

    async def parse(
        self,
        response
    ):

        page = response.meta.get(
            "playwright_page"
        )

        self.logger.info(
            "=" * 70
        )

        self.logger.info(
            "SHEIN PRODUCT DISCOVERY"
        )

        self.logger.info(
            "=" * 70
        )

        self.logger.info(
            f"STATUS: {response.status}"
        )

        self.logger.info(
            f"PAGE URL: {response.url}"
        )

        # ---------------------------------------------------------
        # Validate page
        # ---------------------------------------------------------

        if page is None:

            self.logger.error(
                "PLAYWRIGHT PAGE NOT FOUND"
            )

            return

        try:

            # =====================================================
            # PAGE INFORMATION
            # =====================================================

            title = await page.title()

            self.logger.info(
                f"PAGE TITLE: {title}"
            )

            self.logger.info(
                "PLAYWRIGHT PAGE FOUND"
            )

            # =====================================================
            # NETWORK STATUS
            # =====================================================

            interceptor = getattr(
                page,
                "_pricing_interceptor",
                None
            )

            if interceptor:

                network_responses = (
                    interceptor.get_responses()
                )

            else:

                network_responses = []

            self.logger.info(
                "=" * 70
            )

            self.logger.info(
                "NETWORK CAPTURE"
            )

            self.logger.info(
                "=" * 70
            )

            self.logger.info(
                "Captured network responses: "
                f"{len(network_responses)}"
            )

            # -----------------------------------------------------
            # Print a small diagnostic summary
            # -----------------------------------------------------

            xhr_count = 0
            fetch_count = 0
            json_count = 0

            for network_response in (
                network_responses
            ):

                resource_type = (
                    network_response.get(
                        "resource_type",
                        ""
                    )
                )

                content_type = (
                    network_response.get(
                        "content_type",
                        ""
                    )
                )

                if resource_type == "xhr":

                    xhr_count += 1

                elif resource_type == "fetch":

                    fetch_count += 1

                if "json" in content_type.lower():

                    json_count += 1

            self.logger.info(
                f"XHR responses: {xhr_count}"
            )

            self.logger.info(
                f"FETCH responses: {fetch_count}"
            )

            self.logger.info(
                f"JSON responses: {json_count}"
            )

            # =====================================================
            # WAIT FOR PRODUCT CARDS
            # =====================================================

            try:

                await page.wait_for_selector(
                    "[class*='product-card']",
                    timeout=30000
                )

                self.logger.info(
                    "PRODUCT CARDS DETECTED"
                )

            except Exception as e:

                self.logger.warning(
                    "Product-card selector "
                    f"wait failed: {repr(e)}"
                )

            # =====================================================
            # DYNAMIC CONTENT
            # =====================================================

            await page.wait_for_timeout(
                2500
            )

            # =====================================================
            # SMALL SCROLL
            # =====================================================

            await page.mouse.wheel(
                0,
                random.randint(
                    500,
                    800
                )
            )

            await page.wait_for_timeout(
                2000
            )

            # =====================================================
            # GET LATEST NETWORK COUNT
            # =====================================================

            if interceptor:

                network_responses = (
                    interceptor.get_responses()
                )

            self.logger.info(
                "=" * 70
            )

            self.logger.info(
                "NETWORK AFTER PAGE SETTLED"
            )

            self.logger.info(
                f"Network responses available: "
                f"{len(network_responses)}"
            )

            self.logger.info(
                f"XHR responses: "
                f"{sum(1 for r in network_responses if r.get('resource_type') == 'xhr')}"
            )

            self.logger.info(
                f"FETCH responses: "
                f"{sum(1 for r in network_responses if r.get('resource_type') == 'fetch')}"
            )

            self.logger.info(
                f"JSON responses: "
                f"{sum(1 for r in network_responses if 'json' in r.get('content_type', '').lower())}"
            )

            self.logger.info(
                "=" * 70
            )

            # =====================================================
            # SAVE NETWORK CAPTURE
            # =====================================================
            #
            # IMPORTANT:
            #
            # We use the SAME interceptor that was attached
            # before navigation.
            #
            # We DO NOT create another interceptor here.
            #
            # =====================================================

            if interceptor:

                # Give pending Playwright response callbacks
                # a little time to finish reading response bodies.

                await page.wait_for_timeout(
                    1500
                )

                # Refresh the reference one more time.

                network_responses = (
                    interceptor.get_responses()
                )

                self.logger.info(
                    "=" * 70
                )

                self.logger.info(
                    "SAVING NETWORK CAPTURE"
                )

                self.logger.info(
                    f"Final captured responses: "
                    f"{len(network_responses)}"
                )

                interceptor.save(
                    "output/network.json"
                )

                self.logger.info(
                    "[NETWORK] network.json saved successfully"
                )

                self.logger.info(
                    "=" * 70
                )

            else:

                self.logger.warning(
                    "[NETWORK] Interceptor not available. "
                    "network.json was NOT saved."
                )

            # =====================================================
            # PRODUCT EXTRACTION
            # =====================================================

            extractor = ProductExtractor(
                page
            )

            products = await extractor.extract()

            # =====================================================
            # RESULT
            # =====================================================

            self.logger.info(
                "=" * 70
            )

            self.logger.info(
                f"PRODUCTS EXTRACTED: "
                f"{len(products)}"
            )

            self.logger.info(
                "=" * 70
            )

            # =====================================================
            # CONVERT TO PRICING ITEMS
            # =====================================================

            for product in products:

                product_id = (
                    product.get(
                        "product_id",
                        ""
                    )
                    or ""
                ).strip()

                product_name = (
                    product.get(
                        "name",
                        ""
                    )
                    or ""
                ).strip()

                product_url = (
                    product.get(
                        "product_url",
                        ""
                    )
                    or ""
                ).strip()

                price_text = (
                    product.get(
                        "price",
                        ""
                    )
                    or ""
                ).strip()

                parsed_price = (
                    self.parse_price(
                        price_text
                    )
                )

                # =================================================
                # VALIDATE PRICE
                # =================================================

                if parsed_price is None:

                    self.logger.warning(
                        "[SPIDER] Skipping product "
                        "without valid price | "
                        f"name={product_name}"
                    )

                    continue

                # =================================================
                # ITEM
                # =================================================

                item = {

                    "goods_id": product_id,

                    "product_name": product_name,

                    "product_url": product_url,

                    "price": parsed_price,

                    "original_price": None,

                    "discount": None,

                    "source": "SHEIN",

                    "currency": "USD",

                    "availability": "unknown",

                    "scraped_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                # =================================================
                # LOG
                # =================================================

                self.logger.info(
                    "[SPIDER] PRODUCT"
                )

                self.logger.info(
                    f"    goods_id: "
                    f"{product_id}"
                )

                self.logger.info(
                    f"    name: "
                    f"{product_name}"
                )

                self.logger.info(
                    f"    price: "
                    f"{parsed_price}"
                )

                self.logger.info(
                    f"    url: "
                    f"{product_url}"
                )

                # =================================================
                # YIELD
                # =================================================

                yield item

        except Exception as e:

            self.logger.exception(
                f"SPIDER ERROR: {repr(e)}"
            )

        finally:

            # =====================================================
            # CLOSE PAGE
            # =====================================================

            if (
                page
                and not page.is_closed()
            ):

                await page.close()

                self.logger.info(
                    "Playwright page closed."
                )

    # =========================================================
    # PRICE PARSER
    # =========================================================

    @staticmethod
    def parse_price(
        value
    ):

        if value is None:

            return None

        # ---------------------------------------------------------
        # Numeric
        # ---------------------------------------------------------

        if isinstance(
            value,
            (int, float)
        ):

            return float(
                value
            )

        # ---------------------------------------------------------
        # String
        # ---------------------------------------------------------

        value = str(
            value
        ).strip()

        if not value:

            return None

        # ---------------------------------------------------------
        # Remove currency
        # ---------------------------------------------------------

        value = (
            value
            .replace(
                "$",
                ""
            )
            .replace(
                "USD",
                ""
            )
            .replace(
                "usd",
                ""
            )
            .replace(
                ",",
                ""
            )
            .strip()
        )

        # ---------------------------------------------------------
        # Numeric extraction
        # ---------------------------------------------------------

        match = re.search(
            r"\d+(?:\.\d{1,2})?",
            value
        )

        if not match:

            return None

        try:

            return float(
                match.group(0)
            )

        except ValueError:

            return None

    # =========================================================
    # ERRBACK
    # =========================================================

    async def errback_close_page(
        self,
        failure
    ):

        page = failure.request.meta.get(
            "playwright_page"
        )

        if (
            page
            and not page.is_closed()
        ):

            await page.close()

        self.logger.error(
            f"REQUEST FAILED: "
            f"{repr(failure)}"
        )