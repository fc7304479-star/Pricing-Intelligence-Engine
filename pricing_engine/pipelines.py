from itemadapter import ItemAdapter


class PricingEnginePipeline:

    def __init__(self, storage):

        self.storage = storage

    # =========================================================
    # FROM CRAWLER
    # =========================================================

    @classmethod
    def from_crawler(cls, crawler):

        storage = crawler.settings.get(
            "CLICKHOUSE_STORAGE"
        )

        if storage is None:

            raise RuntimeError(
                "CLICKHOUSE_STORAGE is not configured"
            )

        return cls(storage)

    # =========================================================
    # PROCESS ITEM
    # =========================================================

    def process_item(self, item, spider=None):

        data = ItemAdapter(item).asdict()

        goods_id = str(
            data.get("goods_id") or ""
        ).strip()

        price = data.get("price")

        product_name = str(
            data.get("product_name") or ""
        ).strip()

        availability = str(
            data.get("availability") or ""
        ).strip()

        spider_name = (
            spider.name
            if spider
            else "unknown"
        )

        if spider:

            spider.logger.info(
                "[PIPELINE] Processing | "
                f"goods_id={goods_id} | "
                f"name={product_name} | "
                f"status={availability} | "
                f"price={price}"
            )

        # =====================================================
        # PRODUCT IDENTITY VALIDATION
        # =====================================================

        # A product without goods_id cannot safely receive
        # a normalized product identity.
        #
        # IMPORTANT:
        # Never create:
        #
        #     SHEIN-
        #
        # for an empty goods_id.

        if not goods_id:

            if spider:

                spider.logger.warning(
                    "[PIPELINE] Skipping normalized storage "
                    "because goods_id is empty"
                )

            return item

        # =====================================================
        # NORMALIZED CLICKHOUSE STORAGE
        # =====================================================

        try:

            stored = self.storage.store_normalized(
                data
            )

            if stored:

                if spider:

                    spider.logger.info(
                        "[PIPELINE] Normalized storage "
                        "successful | "
                        f"goods_id={goods_id}"
                    )

            else:

                if spider:

                    spider.logger.warning(
                        "[PIPELINE] Normalized storage "
                        "returned False | "
                        f"goods_id={goods_id}"
                    )

        except Exception as e:

            if spider:

                spider.logger.error(
                    "[PIPELINE] Normalized ClickHouse "
                    "insert failed | "
                    f"goods_id={goods_id} | "
                    f"error={repr(e)}"
                )

            else:

                print(
                    "[PIPELINE] Normalized ClickHouse "
                    f"insert failed: {repr(e)}"
                )

        return item

    # =========================================================
    # CLOSE SPIDER
    # =========================================================

    def close_spider(self, spider=None):

        if spider:

            spider.logger.info(
                "[PIPELINE] Pricing normalized pipeline closed"
            )

        else:

            print(
                "[PIPELINE] Pricing normalized pipeline closed"
            )