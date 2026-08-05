from playwright.async_api import Browser, BrowserContext, Page


class BrowserManager:

    def __init__(self):
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def attach(self, page: Page):
        self.page = page
        self.context = page.context
        self.browser = self.context.browser

    async def close(self):
        """
        Scrapy-Playwright handles closing.
        """
        return