import scrapy


class PricingItem(scrapy.Item):
    # Product Information
    product_name = scrapy.Field()
    product_url = scrapy.Field()
    sku = scrapy.Field()

    # Pricing
    base_price = scrapy.Field()
    final_price = scrapy.Field()
    currency = scrapy.Field()

    # Discount Information
    discount = scrapy.Field()
    coupon = scrapy.Field()

    # Checkout
    shipping = scrapy.Field()
    tax = scrapy.Field()

    # Metadata
    timestamp = scrapy.Field()
    source = scrapy.Field()

    # Raw Data
    raw_json = scrapy.Field()