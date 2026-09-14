import json
import time

from pricing_engine.queue.redis_queue import RedisQueue
from pricing_engine.storage.clickhouse_client import ClickHouseStorage


class QueueWorker:

    def __init__(self):

        self.queue = RedisQueue()

        self.storage = ClickHouseStorage()

    # =========================================================
    # RUN WORKER
    # =========================================================

    def run(self):

        print("=" * 60)
        print("Queue Worker Started")
        print("=" * 60)

        while True:

            item = self.queue.pop()

            if item is None:

                time.sleep(1)

                continue

            try:

                data = json.loads(item)

                # =================================================
                # NORMALIZE QUEUE DATA
                # =================================================

                # Queue historically uses "title".
                # Normalized ClickHouse storage uses
                # "product_name".

                if not data.get("product_name"):

                    data["product_name"] = (
                        data.get("title")
                        or ""
                    )

                # -------------------------------------------------
                # SOURCE
                # -------------------------------------------------

                if not data.get("source"):

                    data["source"] = (
                        data.get("spider_name")
                        or "SHEIN"
                    )

                # =================================================
                # GOODS ID VALIDATION
                # =================================================

                goods_id = str(
                    data.get("goods_id") or ""
                ).strip()

                if not goods_id:

                    print(
                        "[Worker] Skipped -> "
                        "goods_id is empty"
                    )

                    continue

                # =================================================
                # NORMALIZED STORAGE
                # =================================================

                stored = self.storage.store_normalized(
                    data
                )

                if stored:

                    print(
                        "[Worker] Normalized stored -> "
                        f"{data.get('product_name', '')}"
                    )

                else:

                    print(
                        "[Worker] Storage returned False -> "
                        f"{goods_id}"
                    )

            except json.JSONDecodeError as e:

                print(
                    "[Worker] Invalid JSON -> "
                    f"{repr(e)}"
                )

            except Exception as e:

                print(
                    "[Worker] Processing error -> "
                    f"{repr(e)}"
                )


if __name__ == "__main__":

    worker = QueueWorker()

    worker.run()