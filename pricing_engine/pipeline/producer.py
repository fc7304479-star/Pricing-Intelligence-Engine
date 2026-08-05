import json

from pricing_engine.queue.redis_queue import RedisQueue


class Producer:

    def __init__(self):

        self.queue = RedisQueue()

    # ---------------------------------
    # Publish Product
    # ---------------------------------

    def publish(self, product):

        self.queue.push(

            json.dumps(product)

        )