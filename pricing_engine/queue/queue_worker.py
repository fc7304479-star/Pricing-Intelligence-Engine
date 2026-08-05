import json
import time

from pricing_engine.queue.redis_queue import RedisQueue
from pricing_engine.storage.clickhouse_client import ClickHouseStorage


class QueueWorker:

    def __init__(self):

        self.queue = RedisQueue()

        self.storage = ClickHouseStorage()

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

                self.storage.insert(data)

                print(
                    f"[Worker] Stored -> {data['title']}"
                )

            except Exception as e:

                print(e)