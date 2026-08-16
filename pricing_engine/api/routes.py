from fastapi import APIRouter, HTTPException

from pricing_engine.storage.clickhouse_client import ClickHouseStorage
from pricing_engine.api.schemas import Product


router = APIRouter()

storage = ClickHouseStorage()


# =========================================================
# HOME
# =========================================================

@router.get("/")
def home():

    return {
        "message": "Pricing Intelligence Engine API"
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
# PRODUCTS
# =========================================================

@router.get("/products")
def get_products():

    try:

        return storage.get_all()

    except Exception as e:

        print("[API] GET /products ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"ClickHouse products query failed: {str(e)}"
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
            "timestamp": ""
        }

        storage.insert(data)

        return {
            "status": "success",
            "message": "Product stored successfully",
            "product": data
        }

    except Exception as e:

        print("[API] POST /products ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to store product: {str(e)}"
        )


# =========================================================
# COUNT
# =========================================================

@router.get("/products/count")
def get_product_count():

    try:

        return {
            "count": storage.count()
        }

    except Exception as e:

        print("[API] COUNT ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to count products: {str(e)}"
        )


# =========================================================
# LATEST
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

        print("[API] LATEST ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch latest product: {str(e)}"
        )


# =========================================================
# SEARCH
# =========================================================

@router.get("/products/search")
def search_products(keyword: str):

    try:

        data = storage.get_all()

        keyword = keyword.lower()

        results = []

        for item in data:

            title = str(
                item.get("title", "")
            ).lower()

            if keyword in title:

                results.append(item)

        return results

    except Exception as e:

        print("[API] SEARCH ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to search products: {str(e)}"
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
                "lowest_price": 0
            }

        prices = []

        for item in data:

            try:

                prices.append(
                    float(item.get("price", 0))
                )

            except (
                ValueError,
                TypeError
            ):
                continue

        if not prices:

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

    except Exception as e:

        print("[API] GET /stats ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"ClickHouse stats query failed: {str(e)}"
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
        "status": "Running"
    }