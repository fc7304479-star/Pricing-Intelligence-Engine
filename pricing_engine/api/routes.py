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
# GET NORMALIZED PRODUCTS
#
# Returns ONE logical row per product with its latest
# available price observation.
# =========================================================

@router.get("/products")
def get_products():

    try:

        return storage.get_normalized_products()

    except Exception as e:

        print(
            "[API] GET /products ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch normalized products",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# ADD NORMALIZED PRODUCT
# =========================================================

@router.post("/products")
def add_product(product: Product):

    try:

        data = {
            "goods_id": product.goods_id,
            "product_name": product.product_name,
            "product_url": product.product_url,
            "price": product.price,
            "original_price": product.original_price,
            "discount": product.discount,
            "source": product.source,
            "currency": product.currency,
            "availability": product.availability,
            "scraped_at": product.scraped_at,
        }

        stored = storage.store_normalized(
            data
        )

        if not stored:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Product was not stored",
                    "message": "goods_id is required",
                },
            )

        return {
            "status": "success",
            "message": "Product stored in normalized storage",
            "product": data,
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] POST /products ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to store normalized product",
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
            "count": storage.normalized_product_count()
        }

    except Exception as e:

        print(
            "[API] GET /products/count ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to count normalized products",
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

        data = storage.get_normalized_products()

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

        keyword = keyword.lower().strip()

        if not keyword:

            return []

        data = storage.get_normalized_products()

        results = []

        for item in data:

            product_name = str(
                item.get(
                    "product_name",
                    ""
                )
            ).lower()

            source_product_id = str(
                item.get(
                    "source_product_id",
                    ""
                )
            ).lower()

            source = str(
                item.get(
                    "source",
                    ""
                )
            ).lower()

            if (
                keyword in product_name
                or keyword in source_product_id
                or keyword in source
            ):

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
# PRICE OBSERVATIONS
#
# Returns complete normalized price history.
# =========================================================

@router.get("/observations")
def get_observations():

    try:

        return storage.get_observations()

    except Exception as e:

        print(
            "[API] GET /observations ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch price observations",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# STATISTICS
#
# Calculated from NORMALIZED products.
# =========================================================

@router.get("/stats")
def stats():

    try:

        data = storage.get_normalized_products()

        total_products = len(data)

        prices = []

        for item in data:

            price = item.get("price")

            if price is None:

                continue

            try:

                prices.append(
                    float(price)
                )

            except (
                ValueError,
                TypeError,
            ):

                continue

        if not prices:

            return {
                "total_products": total_products,
                "average_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
            }

        return {
            "total_products": total_products,

            "average_price": round(
                sum(prices) / len(prices),
                2,
            ),

            "highest_price": max(
                prices
            ),

            "lowest_price": min(
                prices
            ),
        }

    except Exception as e:

        print(
            "[API] GET /stats ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to calculate normalized statistics",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# NORMALIZED CATALOG
#
# Optional endpoint for catalog-only data.
# =========================================================

@router.get("/catalog")
def get_catalog():

    try:

        return storage.get_catalog()

    except Exception as e:

        print(
            "[API] GET /catalog ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch product catalog",
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# NORMALIZED COUNTS
# =========================================================

@router.get("/normalized/counts")
def normalized_counts():

    try:

        return storage.normalized_counts()

    except Exception as e:

        print(
            "[API] GET /normalized/counts ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch normalized counts",
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
        "data_model": "Normalized",
        "status": "Running",
    }