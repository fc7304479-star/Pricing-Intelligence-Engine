"""
Pricing Intelligence Engine

Sprint 2
---------
Proxy Rotation
Fingerprint Spoofing
Persistent Sessions
"""

BOT_NAME = "pricing_engine"

SPIDER_MODULES = [
    "pricing_engine.spiders"
]

NEWSPIDER_MODULE = "pricing_engine.spiders"

# ----------------------------------------------------
# Robots
# ----------------------------------------------------

ROBOTSTXT_OBEY = False

# ----------------------------------------------------
# Performance
# ----------------------------------------------------

CONCURRENT_REQUESTS = 4

CONCURRENT_REQUESTS_PER_DOMAIN = 2

DOWNLOAD_DELAY = 2

RANDOMIZE_DOWNLOAD_DELAY = True

DOWNLOAD_TIMEOUT = 60

RETRY_ENABLED = True

RETRY_TIMES = 5

COOKIES_ENABLED = True

TELNETCONSOLE_ENABLED = False

# ----------------------------------------------------
# Default Headers
# ----------------------------------------------------

DEFAULT_REQUEST_HEADERS = {

    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
    "en-US,en;q=0.9",

    "Accept-Encoding":
    "gzip, deflate, br",

    "Connection":
    "keep-alive",

}

# ----------------------------------------------------
# Playwright
# ----------------------------------------------------

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

PLAYWRIGHT_LAUNCH_OPTIONS = {

    "headless": False,

    "slow_mo": 150,

    "args": [

        "--disable-blink-features=AutomationControlled",

        "--disable-dev-shm-usage",

        "--disable-web-security",

        "--no-first-run",

        "--disable-infobars",

        "--start-maximized",

    ],

}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000

# ----------------------------------------------------
# Browser Context
# ----------------------------------------------------

PLAYWRIGHT_CONTEXTS = {

    "default": {

        "viewport": {

            "width": 1920,

            "height": 1080,

        },

        "ignore_https_errors": True,

        "java_script_enabled": True,

        "locale": "en-US",

        "timezone_id": "America/New_York",

    }

}

# ----------------------------------------------------
# Downloader Middlewares
# ----------------------------------------------------

DOWNLOADER_MIDDLEWARES = {

    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,

}

# ----------------------------------------------------
# Pipelines
# ----------------------------------------------------

ITEM_PIPELINES = {

    "pricing_engine.pipelines.PricingEnginePipeline": 300,

}

# ----------------------------------------------------
# Feed
# ----------------------------------------------------

FEEDS = {

    "output/pricing.json": {

        "format": "json",

        "indent": 4,

        "overwrite": True,

    }

}

# ----------------------------------------------------
# Logging
# ----------------------------------------------------

LOG_LEVEL = "INFO"

FEED_EXPORT_ENCODING = "utf-8"

LOGSTATS_INTERVAL = 30