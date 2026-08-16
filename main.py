from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timezone


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Pricing Intelligence Engine",
    description="Pricing Intelligence API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    # Local frontend
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        # Vercel production
        "https://pricing-intelligence-dashboard-eta.vercel.app",

        # Vercel git-main deployment
        "https://pricing-intelligence-dashboard-git-main-fahad-ab15.vercel.app",

        # Current preview deployment
        "https://pricing-intelligence-dashboard-hx3kyy2fh-fahad-ab15.vercel.app",
    ],

    # Allows future Vercel preview URLs as well
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATA MODEL
# ============================================================

class Product(BaseModel):
    title: str
    price: float
    currency: str = "USD"
    source: str = ""
    url: str = ""
    network: Optional[List[Any]] = None
    timestamp: Optional[str] = ""


# ============================================================
# IN-MEMORY DATABASE
# ============================================================
#
# IMPORTANT:
# This keeps the API simple and removes the /products 500 error.
#
# If your existing backend already has a real database,
# we can connect this API to that database later.
#
# ============================================================

products_db: List[dict] = []


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Pricing Intelligence Engine is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "pricing-intelligence-engine",
    }


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@app.get("/products")
def get_products():
    """
    Return all stored products.
    """

    try:
        return products_db

    except Exception as e:
        print("GET /products ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch products: {str(e)}",
        )


# ============================================================
# STORE PRODUCT
# ============================================================

@app.post("/products")
def create_product(product: Product):

    try:

        product_data = product.model_dump()

        # Default network
        if product_data.get("network") is None:
            product_data["network"] = []

        # Timestamp
        if not product_data.get("timestamp"):
            product_data["timestamp"] = datetime.now(
                timezone.utc
            ).isoformat()

        products_db.append(product_data)

        return {
            "status": "success",
            "message": "Product stored successfully",
            "product": product_data,
        }

    except Exception as e:

        print("POST /products ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to store product: {str(e)}",
        )


# ============================================================
# STATISTICS
# ============================================================

@app.get("/stats")
def get_stats():

    try:

        if not products_db:

            return {
                "total_products": 0,
                "average_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
            }

        prices = []

        for product in products_db:

            try:
                price = float(product.get("price", 0))
                prices.append(price)

            except (ValueError, TypeError):
                continue

        if not prices:

            return {
                "total_products": len(products_db),
                "average_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
            }

        return {
            "total_products": len(products_db),

            "average_price": round(
                sum(prices) / len(prices),
                2,
            ),

            "highest_price": max(prices),

            "lowest_price": min(prices),
        }

    except Exception as e:

        print("GET /stats ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to calculate statistics: {str(e)}",
        )


# ============================================================
# DELETE ALL PRODUCTS
# ============================================================
#
# Optional utility endpoint for testing.
#
# ============================================================

@app.delete("/products")
def delete_all_products():

    try:

        products_db.clear()

        return {
            "status": "success",
            "message": "All products deleted",
        }

    except Exception as e:

        print("DELETE /products ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to delete products: {str(e)}",
        )


# ============================================================
# RUN LOCALLY
# ============================================================
#
# Start with:
#
# uvicorn main:app --reload --port 8001
#
# ============================================================