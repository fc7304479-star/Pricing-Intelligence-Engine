import json
import redis


def main():

    client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )

    product = {
        "title": "Demo Product",
        "price": "25.00",
        "currency": "USD",
        "url": "https://demowebshop.tricentis.com/",
    }

    client.lpush(
        "pricing_queue",
        json.dumps(product)
    )

    print("✅ Product pushed into Redis Queue")

    item = client.rpop("pricing_queue")

    print("\nReceived from Queue:\n")

    print(json.loads(item))


if __name__ == "__main__":
    main()