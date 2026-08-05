from pricing_engine.queue.redis_queue import RedisQueue
from pricing_engine.storage.clickhouse_client import ClickHouseClient


class Consumer:

    def __init__(self):

        self.queue = RedisQueue()

        self.database = ClickHouseClient()

        self.database.create_table()

    # ---------------------------------
    # Consume One Product
    # ---------------------------------

    def consume(self):

        product = self.queue.pop()

        if product is None:
            return None

        self.database.insert_product(product)

        return product

    # ---------------------------------
    # Consume All Products
    # ---------------------------------

    def consume_all(self):

        count = 0

        while not self.queue.empty():

            product = self.consume()

            if product:
                count += 1

        return count