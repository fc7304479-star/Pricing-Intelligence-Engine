BOT_NAME = "pricing_engine"

SPIDER_MODULES = [
    "pricing_engine.spiders"
]

NEWSPIDER_MODULE = (
    "pricing_engine.spiders"
)

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 1

CONCURRENT_REQUESTS_PER_DOMAIN = 1

DOWNLOAD_DELAY = 2

DOWNLOAD_TIMEOUT = 90


# =========================================================
# PLAYWRIGHT
# =========================================================

DOWNLOAD_HANDLERS = {

    "http":
        "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",

    "https":
        "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",

}

TWISTED_REACTOR = (
    "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
)

PLAYWRIGHT_BROWSER_TYPE = "chromium"

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000

PLAYWRIGHT_INCLUDE_PAGE = True


# =========================================================
# PIPELINE
# =========================================================

ITEM_PIPELINES = {

    "pricing_engine.pipelines.PricingEnginePipeline":
        300,

}


# =========================================================
# CLICKHOUSE
# =========================================================

from pricing_engine.storage.clickhouse_client import (
    ClickHouseStorage
)

CLICKHOUSE_STORAGE = ClickHouseStorage()

CLICKHOUSE_STORAGE.create_table()


# =========================================================
# FEEDS
# =========================================================

FEEDS = {

    "output/pricing.json": {

        "format": "json",

        "encoding": "utf-8",

        "indent": 2,

        "overwrite": True,

    }

}


FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = "INFO"

TELNETCONSOLE_ENABLED = False