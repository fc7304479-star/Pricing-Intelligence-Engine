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

        data = ItemAdapter(
            item
        ).asdict()

        goods_id = data.get(
            "goods_id"
        )

        price = data.get(
            "price"
        )

        status = data.get(
            "availability"
        )

        product_name = data.get(
            "product_name"
        )

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

                f"status={status} | "

                f"price={price}"

            )

        # -----------------------------------------------------
        # Skip products without price
        # -----------------------------------------------------

        if price is None:

            if spider:

                spider.logger.warning(

                    "[PIPELINE] Skipping "
                    "ClickHouse insert for "

                    f"{goods_id} because "
                    "price is None"

                )

            return item

        # -----------------------------------------------------
        # Insert ClickHouse
        # -----------------------------------------------------

        try:

            self.storage.insert(
                data
            )

            if spider:

                spider.logger.info(

                    "[PIPELINE] Inserted "

                    f"{goods_id} into "
                    "ClickHouse"

                )

        except Exception as e:

            if spider:

                spider.logger.error(

                    "[PIPELINE] ClickHouse "
                    "insert failed for "

                    f"{goods_id}: "
                    f"{repr(e)}"

                )

            else:

                print(
                    "[PIPELINE] ClickHouse "
                    f"insert failed: {repr(e)}"
                )

        return item

    # =========================================================
    # CLOSE SPIDER
    # =========================================================

    def close_spider(self, spider=None):

        if spider:

            spider.logger.info(
                "[PIPELINE] Pricing pipeline closed"
            )

        else:

            print(
                "[PIPELINE] Pricing pipeline closed"
            )
