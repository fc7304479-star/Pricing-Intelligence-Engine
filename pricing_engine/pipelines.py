from itemadapter import ItemAdapter
from pricing_engine.storage.clickhouse_client import ClickHouseStorage


class PricingEnginePipeline:

    def __init__(self):
        self.storage = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        pipeline.storage = ClickHouseStorage()
        return pipeline

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        data = {
            "title": adapter.get("title", ""),
            "url": adapter.get("url", ""),
            "price": adapter.get("price", 0),
            "source": adapter.get("source", ""),
            "currency": adapter.get("currency", "USD"),
            "network": adapter.get("network", []),
            "timestamp": adapter.get("timestamp", ""),
        }

        self.storage.insert(data)

        spider.logger.info(
            f"[PIPELINE] Stored in ClickHouse: {data['title']}"
        )

        return item