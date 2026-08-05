from bs4 import BeautifulSoup


class LayoutDetector:

    def __init__(self, html):

        self.soup = BeautifulSoup(html, "html.parser")

    def product_title(self):

        selectors = [

            "h1",

            ".product-name",

            ".product-title",

            ".title",

            "[itemprop='name']"

        ]

        for selector in selectors:

            tag = self.soup.select_one(selector)

            if tag:

                return tag.get_text(strip=True)

        return None

    def product_price(self):

        selectors = [

            ".price",

            ".product-price",

            ".actual-price",

            "[itemprop='price']"

        ]

        for selector in selectors:

            tag = self.soup.select_one(selector)

            if tag:

                return tag.get_text(strip=True)

        return None