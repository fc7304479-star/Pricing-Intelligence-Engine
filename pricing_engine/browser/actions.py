from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)


class BrowserActions:
    """
    Centralized Playwright browser actions.

    The spider owns the Page lifecycle.
    This class does NOT close the page.
    """

    def __init__(self, page: Page):

        self.page = page

    # ========================================================
    # PAGE
    # ========================================================

    async def wait_network(
        self,
        timeout: int = 15000
    ):

        try:

            await self.page.wait_for_load_state(
                "networkidle",
                timeout=timeout
            )

        except PlaywrightTimeoutError:

            pass

    async def open_product(
        self,
        url: str
    ):

        await self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=90000
        )

        await self.page.wait_for_timeout(
            2000
        )

    async def get_title(self) -> str:

        try:

            return await self.page.title()

        except Exception:

            return ""

    async def get_url(self) -> str:

        try:

            return self.page.url

        except Exception:

            return ""

    async def get_body_text(self) -> str:

        try:

            return await self.page.locator(
                "body"
            ).inner_text()

        except Exception:

            return ""

    # ========================================================
    # HTML
    # ========================================================

    async def get_html(self) -> str:

        try:

            return await self.page.content()

        except Exception:

            return ""

    # ========================================================
    # SCROLL
    # ========================================================

    async def scroll_page(
        self,
        distance: int = 800
    ):

        try:

            await self.page.evaluate(
                """
                (distance) => {
                    window.scrollBy(0, distance);
                }
                """,
                distance
            )

            await self.page.wait_for_timeout(
                1000
            )

        except Exception:

            pass

    async def scroll_to_bottom(
        self,
        max_scrolls: int = 10
    ):

        for _ in range(max_scrolls):

            try:

                previous_height = await self.page.evaluate(
                    """
                    () => document.body.scrollHeight
                    """
                )

                await self.page.evaluate(
                    """
                    () => {
                        window.scrollTo(
                            0,
                            document.body.scrollHeight
                        );
                    }
                    """
                )

                await self.page.wait_for_timeout(
                    1200
                )

                current_height = await self.page.evaluate(
                    """
                    () => document.body.scrollHeight
                    """
                )

                if current_height == previous_height:

                    break

            except Exception:

                break

    # ========================================================
    # SAFE CHECK
    # ========================================================

    async def is_page_alive(self) -> bool:

        try:

            if self.page.is_closed():

                return False

            await self.page.evaluate(
                "() => true"
            )

            return True

        except Exception:

            return False