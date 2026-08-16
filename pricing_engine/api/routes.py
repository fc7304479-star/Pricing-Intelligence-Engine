from fastapi import APIRouter, HTTPException

from pricing_engine.storage.clickhouse_client import ClickHouseStorage
from pricing_engine.api.schemas import Product


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

    try:
        data = storage.get_all()

        cleaned = []

        for item in data:
            cleaned.append({
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "price": float(item.get("price", 0)),
                "source": str(item.get("source", "")),
                "currency": str(item.get("currency", "USD")),
                "network": str(item.get("network", "[]")),
                "timestamp": str(item.get("timestamp", "")),
                "stored_at": str(item.get("stored_at", ""))
            })

        return cleaned

    except Exception as e:

        print(
            f"[PRODUCTS ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to fetch products",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Add Product
# ---------------------------------------------------

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

        print(
            f"[ADD PRODUCT ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to store product",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Count Products
# ---------------------------------------------------

@router.get("/products/count")
def get_product_count():

    try:

        return {
            "count": storage.count()
        }

    except Exception as e:

        print(
            f"[COUNT ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to count products",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Latest Product
# ---------------------------------------------------

@router.get("/products/latest")
def latest_product():

    try:

        data = storage.get_all()

        if len(data) == 0:
            return {
                "message": "No Products Found"
            }

        return data[-1]

    except Exception as e:

        print(
            f"[LATEST PRODUCT ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to fetch latest product",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Search Products
# ---------------------------------------------------

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

        print(
            f"[SEARCH ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to search products",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Statistics
# ---------------------------------------------------

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
                    float(
                        item.get(
                            "price",
                            0
                        )
                    )
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

        print(
            f"[STATS ERROR] "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to calculate statistics",
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )


# ---------------------------------------------------
# Version
# ---------------------------------------------------

@router.get("/version")
def version():

    return {
        "engine": "Pricing Intelligence Engine",
        "version": "1.0.0",
        "framework": "FastAPI",
        "storage": "ClickHouse",
        "status": "Running"
    }