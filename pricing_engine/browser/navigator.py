class BrowserNavigator:

    def __init__(self, page):
        self.page = page

    async def goto(self, url):

        await self.page.goto(
            url,
            wait_until="domcontentloaded"
        )

    async def click(self, selector):

        await self.page.click(selector)

    async def fill(self, selector, value):

        await self.page.fill(
            selector,
            value
        )

    async def wait(self, ms=2000):

        await self.page.wait_for_timeout(ms)

    async def title(self):

        return await self.page.title()

    async def current_url(self):

        return self.page.url

    async def locator(self, selector):

        return self.page.locator(selector)

    async def evaluate(self, script):

        return await self.page.evaluate(script)

    async def close(self):

        await self.page.close()