from fastapi import APIRouter
from pricing_engine.storage.clickhouse_client import ClickHouseStorage

router = APIRouter()

storage = ClickHouseStorage()


# ---------------------------------------------------
# Home
# ---------------------------------------------------

@router.get("/")
def home():

    return {
        "message": "Pricing Intelligence Engine API"
    }


# ---------------------------------------------------
# Health
# ---------------------------------------------------

@router.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ---------------------------------------------------
# Get All Products
# ---------------------------------------------------

@router.get("/products")
def get_products():

    return storage.get_all()


# ---------------------------------------------------
# Count Products
# ---------------------------------------------------

@router.get("/products/count")
def get_product_count():

    return {
        "count": storage.count()
    }


# ---------------------------------------------------
# Latest Product
# ---------------------------------------------------

@router.get("/products/latest")
def latest_product():

    data = storage.get_all()

    if len(data) == 0:

        return {
            "message": "No Products Found"
        }

    return data[-1]


# ---------------------------------------------------
# Search Products
# ---------------------------------------------------

@router.get("/products/search")
def search_products(keyword: str):

    data = storage.get_all()

    keyword = keyword.lower()

    results = []

    for item in data:

        title = item.get("title", "").lower()

        if keyword in title:

            results.append(item)

    return results


# ---------------------------------------------------
# Statistics
# ---------------------------------------------------

@router.get("/stats")
def stats():

    data = storage.get_all()

    if len(data) == 0:

        return {
            "total_products": 0,
            "average_price": 0,
            "highest_price": 0,
            "lowest_price": 0
        }

    prices = []

    for item in data:

        try:

            prices.append(
                float(item["price"])
            )

        except:

            pass

    if len(prices) == 0:

        return {
            "total_products": len(data),
            "average_price": 0,
            "highest_price": 0,
            "lowest_price": 0
        }

    return {

        "total_products": len(data),

        "average_price": round(
            sum(prices) / len(prices),
            2
        ),

        "highest_price": max(prices),

        "lowest_price": min(prices)
    }


# ---------------------------------------------------
# Version
# ---------------------------------------------------

@router.get("/version")
def version():

    return {

        "engine": "Pricing Intelligence Engine",

        "version": "1.0.0",

        "framework": "FastAPI",

        "storage": "ClickHouse (Mock)",

        "status": "Running"
    }