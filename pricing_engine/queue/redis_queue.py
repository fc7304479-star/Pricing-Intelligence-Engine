import redis


class RedisQueue:

    def __init__(
        self,
        host="localhost",
        port=6379,
        db=0,
        queue_name="pricing_queue",
    ):

        self.queue_name = queue_name

        try:

            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=3,
            )

            # Test Connection
            self.redis.ping()

            self.connected = True

            print("[Redis] Connected")

        except Exception as e:

            self.connected = False

            self.redis = None

            print(f"[Redis] Connection Failed : {e}")

    # ---------------------------------
    # Push
    # ---------------------------------

    def push(self, data):

        if not self.connected:
            return False

        self.redis.rpush(
            self.queue_name,
            data,
        )

        return True

    # ---------------------------------
    # Pop
    # ---------------------------------

    def pop(self):

        if not self.connected:
            return None

        return self.redis.lpop(
            self.queue_name
        )

    # ---------------------------------
    # Queue Size
    # ---------------------------------

    def size(self):

        if not self.connected:
            return 0

        return self.redis.llen(
            self.queue_name
        )