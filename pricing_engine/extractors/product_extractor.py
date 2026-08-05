class ProductExtractor:

    def __init__(self, page):
        self.page = page

    async def extract(self):

        products = self.page.locator(".product-item")

        data = []

        count = await products.count()

        for i in range(count):

            product = products.nth(i)

            name = await product.locator(
                ".product-title"
            ).inner_text()

            href = await product.locator(
                ".product-title a"
            ).get_attribute("href")

            data.append(
                {
                    "name": name,
                    "href": href
                }
            )

        return data