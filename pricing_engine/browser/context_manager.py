from pricing_engine.browser.user_agent import UserAgentManager
from pricing_engine.browser.proxy_manager import ProxyManager


class ContextManager:

    @staticmethod
    async def create(browser):

        user_agent = UserAgentManager.random()

        proxy = ProxyManager.get_proxy()

        context = await browser.new_context(

            user_agent=user_agent,

            viewport={
                "width": 1366,
                "height": 768,
            },

            locale="en-US",

            timezone_id="America/New_York",

            color_scheme="light",

            java_script_enabled=True,

            ignore_https_errors=True,

            proxy=proxy

            if proxy else None

        )

        return context