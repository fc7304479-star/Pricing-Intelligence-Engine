from fastapi import APIRouter, HTTPException

from pricing_engine.storage.clickhouse_client import ClickHouseStorage
from pricing_engine.api.schemas import Product


router = APIRouter()

# =========================================================
# STORAGE
# =========================================================

storage = ClickHouseStorage()
storage.create_table()


# =========================================================
# HOME
# =========================================================

@router.get("/")
def home():
    return {
        "message": "Pricing Intelligence Engine API",
        "status": "running",
    }


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@router.get("/products")
def get_products():

    try:

        products = storage.get_all()

        return products

    except Exception as e:

        print(
            "[API] GET /products ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch products",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# ADD PRODUCT
# =========================================================

@router.post("/products")
def add_product(product: Product):

    try:

        data = {
            "title": product.title,
            "price": product.price,
            "currency": product.currency,
            "source": product.source,
            "url": product.url,
            "network": [],
            "timestamp": "",
        }

        storage.insert(data)

        return {
            "status": "success",
            "message": "Product stored successfully",
            "product": data,
        }

    except Exception as e:

        print(
            "[API] POST /products ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to store product",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# PRODUCT COUNT
# =========================================================

@router.get("/products/count")
def get_product_count():

    try:

        return {
            "count": storage.count()
        }

    except Exception as e:

        print(
            "[API] GET /products/count ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to count products",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# LATEST PRODUCT
# =========================================================

@router.get("/products/latest")
def latest_product():

    try:

        data = storage.get_all()

        if not data:

            return {
                "message": "No Products Found"
            }

        return data[0]

    except Exception as e:

        print(
            "[API] GET /products/latest ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch latest product",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# SEARCH PRODUCTS
# =========================================================

@router.get("/products/search")
def search_products(keyword: str):

    try:

        data = storage.get_all()

        keyword = keyword.lower().strip()

        results = []

        for item in data:

            title = str(
                item.get("title", "")
            ).lower()

            if keyword in title:

                results.append(item)

        return results

    except Exception as e:

        print(
            "[API] GET /products/search ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to search products",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# STATISTICS
# =========================================================

@router.get("/stats")
def stats():

    try:

        data = storage.get_all()

        if not data:

            return {
                "total_products": 0,
                "average_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
            }

        prices = []

        for item in data:

            try:

                price = float(
                    item.get("price", 0)
                )

                prices.append(price)

            except (
                ValueError,
                TypeError,
            ):

                continue

        if not prices:

            return {
                "total_products": len(data),
                "average_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
            }

        return {
            "total_products": len(data),

            "average_price": round(
                sum(prices) / len(prices),
                2,
            ),

            "highest_price": max(prices),

            "lowest_price": min(prices),
        }

    except Exception as e:

        print(
            "[API] GET /stats ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to calculate statistics",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# VERSION
# =========================================================

@router.get("/version")
def version():

    return {
        "engine": "Pricing Intelligence Engine",
        "version": "1.0.0",
        "framework": "FastAPI",
        "storage": "ClickHouse",
        "status": "Running",
    }