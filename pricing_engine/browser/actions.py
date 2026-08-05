from playwright.async_api import Page


class BrowserActions:

    def __init__(self, page: Page):
        self.page = page

    async def open_product(self, url: str):

        await self.page.goto(
            url,
            wait_until="domcontentloaded"
        )

        await self.page.wait_for_timeout(2000)

    async def fill_gift_card(self):

        await self.page.fill(
            "#giftcard_2_RecipientName",
            "John"
        )

        await self.page.fill(
            "#giftcard_2_RecipientEmail",
            "john@example.com"
        )

        await self.page.fill(
            "#giftcard_2_SenderName",
            "AI Bot"
        )

        await self.page.fill(
            "#giftcard_2_SenderEmail",
            "bot@example.com"
        )

        await self.page.fill(
            "#giftcard_2_Message",
            "Sprint 1 Testing"
        )

    async def add_to_cart(self):

        await self.page.click(
            "#add-to-cart-button-2"
        )

        await self.page.wait_for_timeout(3000)