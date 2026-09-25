from fastapi import APIRouter, HTTPException

from pricing_engine.storage.clickhouse_client import ClickHouseStorage
from pricing_engine.api.schemas import Product
from pricing_engine.intelligence.competitive_price_changes import CompetitivePriceChangeService
from pricing_engine.intelligence.price_trend import PriceTrendService
from pricing_engine.intelligence.pricing_signals import PricingSignalService
from pricing_engine.intelligence.price_comparison import PriceComparisonService


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
# PRICE HISTORY FOR ONE PRODUCT
#
# Returns the complete normalized price observation
# history for a specific product.
#
# Example:
# /products/SHEIN-43668346/price-history
# =========================================================

@router.get("/products/{product_id}/price-history")
def get_product_price_history(product_id: str):

    try:

        product_id = product_id.strip()

        if not product_id:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Product ID is required"
                },
            )

        history = storage.get_price_history(
            product_id
        )

        if not history:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Product price history not found",
                    "product_id": product_id,
                },
            )

        return {
            "product_id": product_id,
            "observation_count": len(history),
            "observations": history,
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] GET /products/{product_id}/price-history ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to fetch product price history",
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
# PRICE CHANGE DETECTION
#
# Compares consecutive price observations for each product.
#
# Returns:
# - previous price
# - current price
# - absolute change
# - percentage change
# - direction
# - observation timestamps
# =========================================================

@router.get("/price-changes")
def get_price_changes():

    try:

        observations = storage.get_observations()

        # -----------------------------------------------------
        # Group observations by product
        # -----------------------------------------------------

        grouped = {}

        for item in observations:

            product_id = item.get(
                "product_id"
            )

            if not product_id:

                continue

            grouped.setdefault(
                product_id,
                []
            ).append(item)

        changes = []

        # -----------------------------------------------------
        # Compare consecutive observations
        # -----------------------------------------------------

        for product_id, product_observations in grouped.items():

            # Sort oldest -> newest
            product_observations.sort(
                key=lambda x: (
                    x.get(
                        "observed_at"
                    )
                    or ""
                )
            )

            for index in range(
                1,
                len(product_observations)
            ):

                previous = product_observations[
                    index - 1
                ]

                current = product_observations[
                    index
                ]

                previous_price = previous.get(
                    "price"
                )

                current_price = current.get(
                    "price"
                )

                # -------------------------------------------------
                # Skip observations without valid prices
                # -------------------------------------------------

                if (
                    previous_price is None
                    or current_price is None
                ):

                    continue

                try:

                    previous_price = float(
                        previous_price
                    )

                    current_price = float(
                        current_price
                    )

                except (
                    ValueError,
                    TypeError,
                ):

                    continue

                # -------------------------------------------------
                # Calculate price movement
                # -------------------------------------------------

                change_amount = (
                    current_price
                    - previous_price
                )

                if previous_price == 0:

                    change_percent = None

                else:

                    change_percent = (
                        (
                            change_amount
                            / previous_price
                        )
                        * 100
                    )

                # -------------------------------------------------
                # Determine direction
                # -------------------------------------------------

                if change_amount > 0:

                    direction = "increase"

                elif change_amount < 0:

                    direction = "decrease"

                else:

                    direction = "unchanged"

                # -------------------------------------------------
                # Add detected change
                # -------------------------------------------------

                changes.append({

                    "product_id": product_id,

                    "source": current.get(
                        "source"
                    ),

                    "source_product_id": current.get(
                        "source_product_id"
                    ),

                    "previous_price": round(
                        previous_price,
                        2
                    ),

                    "current_price": round(
                        current_price,
                        2
                    ),

                    "change_amount": round(
                        change_amount,
                        2
                    ),

                    "change_percent": (
                        round(
                            change_percent,
                            2
                        )
                        if change_percent is not None
                        else None
                    ),

                    "direction": direction,

                    "previous_observed_at": previous.get(
                        "observed_at"
                    ),

                    "current_observed_at": current.get(
                        "observed_at"
                    ),

                })

        # -----------------------------------------------------
        # Newest changes first
        # -----------------------------------------------------

        changes.sort(
            key=lambda x: (
                x.get(
                    "current_observed_at"
                )
                or ""
            ),
            reverse=True,
        )

        return changes

    except Exception as e:

        print(
            "[API] GET /price-changes ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to calculate price changes",
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


@router.get("/competitive-products/{canonical_product_id}/signals")
def get_competitive_product_pricing_signals(
    canonical_product_id: str,
):
    """
    Return rule-based pricing signals for a matched
    competitive product.
    """

    matches = storage.get_product_matches(
        canonical_product_id
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Competitive product not found",
                "canonical_product_id": canonical_product_id,
            },
        )

    products = []

    for match in matches:
        source = str(
            match.get("source") or ""
        ).strip().upper()

        source_product_id = str(
            match.get("source_product_id") or ""
        ).strip()

        if not source or not source_product_id:
            continue

        history = storage.get_price_history(
            f"{source}-{source_product_id}"
        )

        products.append(
            {
                "source": source,
                "source_product_id": source_product_id,
                "match_method": match.get(
                    "match_method"
                ),
                "match_confidence": match.get(
                    "match_confidence"
                ),
                "history": history,
            }
        )

    latest_products = []

    for product in products:
        history = product.get("history") or []

        if not history:
            continue

        latest = history[-1]

        latest_products.append(
            {
                "source": product.get("source", ""),
                "source_product_id": product.get(
                    "source_product_id", ""
                ),
                "price": latest.get("price"),
                "currency": latest.get(
                    "currency",
                    "USD",
                ),
                "availability": latest.get(
                    "availability",
                    "unknown",
                ),
            }
        )

    comparison_service = PriceComparisonService(
        reference_source="AMAZON"
    )

    comparison = (
        comparison_service.compare_products(
            latest_products
        )
    )

    reference_product = comparison.get(
        "reference_product"
    )

    if reference_product is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Reference product not found",
                "canonical_product_id": (
                    canonical_product_id
                ),
                "reference_source": "AMAZON",
            },
        )

    change_service = (
        CompetitivePriceChangeService()
    )

    price_changes = (
        change_service.calculate_competitive_changes(
            products
        )
    )

    signal_service = PricingSignalService()

    result = signal_service.analyze(
        reference_price=reference_product.get(
            "price"
        ),
        market_average=comparison.get(
            "market_average"
        ),
        price_changes=price_changes,
    )

    result["canonical_product_id"] = (
        canonical_product_id
    )

    return result

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


# =========================================================
# COMPETITIVE PRODUCT SNAPSHOT
# =========================================================

@router.get("/competitive-products/{canonical_product_id}")
def get_competitive_product(canonical_product_id: str):

    try:

        result = storage.get_competitive_product(
            canonical_product_id
        )

        if result is None:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Competitive product not found",
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        products = result.get(
            "products",
            [],
        )

        if not products:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No competitive pricing data found"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        # -------------------------------------------------
        # MARKET AVERAGE
        # -------------------------------------------------

        valid_prices = []

        for product in products:

            price = product.get("price")

            if price is None:
                continue

            try:
                price = float(price)
            except (
                TypeError,
                ValueError,
            ):
                continue

            if price < 0:
                continue

            valid_prices.append(price)

        market_average = None

        if valid_prices:

            market_average = round(
                sum(valid_prices)
                / len(valid_prices),
                2,
            )

        # -------------------------------------------------
        # REFERENCE SOURCE
        # -------------------------------------------------

        reference_source = "AMAZON"

        reference_product = None

        for product in products:

            source = str(
                product.get("source")
                or ""
            ).strip().upper()

            if source == reference_source:

                reference_product = product

                break

        # -------------------------------------------------
        # REFERENCE PRICE
        # -------------------------------------------------

        reference_price = None

        if reference_product is not None:

            reference_price = (
                reference_product.get("price")
            )

            if reference_price is not None:

                try:
                    reference_price = float(
                        reference_price
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    reference_price = None

        # -------------------------------------------------
        # PRICE DIFFERENCE %
        # -------------------------------------------------

        comparison_products = []

        for product in products:

            item = dict(product)

            price = item.get("price")

            difference_percent = None

            if (
                price is not None
                and market_average is not None
                and market_average != 0
            ):

                try:

                    price = float(price)

                    difference_percent = round(
                        (
                            (
                                price
                                - market_average
                            )
                            / market_average
                        )
                        * 100,
                        2,
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    difference_percent = None

            item[
                "price_difference_percent"
            ] = difference_percent

            comparison_products.append(
                item
            )

        # -------------------------------------------------
        # LAST UPDATED
        # -------------------------------------------------

        observed_times = []

        for product in comparison_products:

            observed_at = product.get(
                "observed_at"
            )

            if observed_at:

                observed_times.append(
                    str(observed_at)
                )

        last_updated = None

        if observed_times:

            last_updated = max(
                observed_times
            )

        # -------------------------------------------------
        # REFERENCE VS MARKET
        # -------------------------------------------------

        reference_difference_percent = None

        if (
            reference_price is not None
            and market_average is not None
            and market_average != 0
        ):

            reference_difference_percent = round(
                (
                    (
                        reference_price
                        - market_average
                    )
                    / market_average
                )
                * 100,
                2,
            )

        return {
            "canonical_product_id": (
                canonical_product_id
            ),
            "reference_source": (
                reference_source
            ),
            "reference_price": (
                reference_price
            ),
            "market_average": (
                market_average
            ),
            "reference_difference_percent": (
                reference_difference_percent
            ),
            "last_updated": (
                last_updated
            ),
            "products": (
                comparison_products
            ),
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] GET /competitive-products ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "Unable to fetch competitive "
                    "product snapshot"
                ),
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# COMPETITIVE PRODUCT PRICE HISTORY
# =========================================================

@router.get(
    "/competitive-products/{canonical_product_id}/price-history"
)
def get_competitive_product_price_history(
    canonical_product_id: str,
):

    try:

        canonical_product_id = str(
            canonical_product_id or ""
        ).strip()

        if not canonical_product_id:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": (
                        "canonical_product_id is required"
                    ),
                },
            )

        matches = storage.get_product_matches(
            canonical_product_id
        )

        if not matches:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No source products are linked "
                        "to this canonical product"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        products = []

        for match in matches:

            source = str(
                match.get("source")
                or ""
            ).strip().upper()

            source_product_id = str(
                match.get("source_product_id")
                or ""
            ).strip()

            if not source_product_id:
                continue

            history = storage.get_price_history(
                f"{source}-{source_product_id}"
            )

            # -------------------------------------------------
            # IMPORTANT:
            # get_price_history() is source-product based.
            # We filter the result to the exact source product.
            # -------------------------------------------------

            filtered_history = []

            for observation in history:

                observation_source_product_id = str(
                    observation.get(
                        "source_product_id"
                    )
                    or ""
                ).strip()

                if (
                    observation_source_product_id
                    and observation_source_product_id
                    != source_product_id
                ):
                    continue

                filtered_history.append(
                    {
                        "price": observation.get(
                            "price"
                        ),
                        "original_price": observation.get(
                            "original_price"
                        ),
                        "discount": observation.get(
                            "discount"
                        ),
                        "currency": observation.get(
                            "currency",
                            "USD",
                        ),
                        "availability": observation.get(
                            "availability",
                            "unknown",
                        ),
                        "observed_at": observation.get(
                            "observed_at"
                        ),
                    }
                )

            products.append(
                {
                    "source": source,
                    "source_product_id": (
                        source_product_id
                    ),
                    "match_method": match.get(
                        "match_method"
                    ),
                    "match_confidence": match.get(
                        "match_confidence"
                    ),
                    "history": filtered_history,
                }
            )

        if not products:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No competitive price history found"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        # -------------------------------------------------
        # SORT SOURCES
        # -------------------------------------------------

        source_order = {
            "AMAZON": 1,
            "WALMART": 2,
            "BESTBUY": 3,
        }

        products.sort(
            key=lambda item: (
                source_order.get(
                    item["source"],
                    99,
                ),
                item["source"],
            )
        )

        # -------------------------------------------------
        # GLOBAL LATEST OBSERVATION
        # -------------------------------------------------

        latest_times = []

        for product in products:

            for observation in product["history"]:

                observed_at = observation.get(
                    "observed_at"
                )

                if observed_at:

                    latest_times.append(
                        str(observed_at)
                    )

        last_updated = None

        if latest_times:

            last_updated = max(
                latest_times
            )

        return {
            "canonical_product_id": (
                canonical_product_id
            ),
            "reference_source": "AMAZON",
            "last_updated": last_updated,
            "products": products,
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] GET "
            "/competitive-products/"
            "{canonical_product_id}/price-history "
            "ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "Unable to fetch competitive "
                    "price history"
                ),
                "type": type(e).__name__,
                "message": str(e),
            },
        )



# =========================================================
# COMPETITIVE PRODUCT PRICE CHANGES
# =========================================================

@router.get(
    "/competitive-products/{canonical_product_id}/price-changes"
)
def get_competitive_product_price_changes(
    canonical_product_id: str,
):

    try:

        canonical_product_id = str(
            canonical_product_id or ""
        ).strip()

        if not canonical_product_id:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": (
                        "canonical_product_id is required"
                    ),
                },
            )

        matches = storage.get_product_matches(
            canonical_product_id
        )

        if not matches:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No source products are linked "
                        "to this canonical product"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        products = []

        for match in matches:

            source = str(
                match.get("source")
                or ""
            ).strip().upper()

            source_product_id = str(
                match.get("source_product_id")
                or ""
            ).strip()

            if not source_product_id:
                continue

            history = storage.get_price_history(
                f"{source}-{source_product_id}"
            )

            filtered_history = []

            for observation in history:

                observation_source_product_id = str(
                    observation.get(
                        "source_product_id"
                    )
                    or ""
                ).strip()

                if (
                    observation_source_product_id
                    and observation_source_product_id
                    != source_product_id
                ):
                    continue

                filtered_history.append(
                    {
                        "price": observation.get(
                            "price"
                        ),
                        "observed_at": observation.get(
                            "observed_at"
                        ),
                    }
                )

            products.append(
                {
                    "source": source,
                    "source_product_id": (
                        source_product_id
                    ),
                    "match_method": match.get(
                        "match_method"
                    ),
                    "match_confidence": match.get(
                        "match_confidence"
                    ),
                    "history": filtered_history,
                }
            )

        if not products:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No competitive price history found"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        service = CompetitivePriceChangeService()

        changes = service.calculate_competitive_changes(
            products
        )

        source_order = {
            "AMAZON": 1,
            "WALMART": 2,
            "BESTBUY": 3,
        }

        changes.sort(
            key=lambda item: (
                source_order.get(
                    item.get("source"),
                    99,
                ),
                item.get("source", ""),
            )
        )

        latest_times = []

        for item in changes:

            current = item.get("current") or {}

            observed_at = current.get(
                "observed_at"
            )

            if observed_at:
                latest_times.append(
                    str(observed_at)
                )

        last_updated = None

        if latest_times:
            last_updated = max(latest_times)

        return {
            "canonical_product_id": (
                canonical_product_id
            ),
            "reference_source": "AMAZON",
            "last_updated": last_updated,
            "products": changes,
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] GET "
            "/competitive-products/"
            "{canonical_product_id}/price-changes "
            "ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "Unable to calculate competitive "
                    "price changes"
                ),
                "type": type(e).__name__,
                "message": str(e),
            },
        )


# =========================================================
# COMPETITIVE PRODUCT PRICE TRENDS
# =========================================================

@router.get(
    "/competitive-products/{canonical_product_id}/price-trends"
)
def get_competitive_product_price_trends(
    canonical_product_id: str,
):

    try:

        canonical_product_id = str(
            canonical_product_id or ""
        ).strip()

        if not canonical_product_id:

            raise HTTPException(
                status_code=400,
                detail={
                    "error": (
                        "canonical_product_id is required"
                    ),
                },
            )

        matches = storage.get_product_matches(
            canonical_product_id
        )

        if not matches:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No source products are linked "
                        "to this canonical product"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        products = []

        for match in matches:

            source = str(
                match.get("source")
                or ""
            ).strip().upper()

            source_product_id = str(
                match.get("source_product_id")
                or ""
            ).strip()

            if not source_product_id:
                continue

            history = storage.get_price_history(
                f"{source}-{source_product_id}"
            )

            filtered_history = []

            for observation in history:

                observation_source_product_id = str(
                    observation.get(
                        "source_product_id"
                    )
                    or ""
                ).strip()

                if (
                    observation_source_product_id
                    and observation_source_product_id
                    != source_product_id
                ):
                    continue

                filtered_history.append(
                    {
                        "price": observation.get(
                            "price"
                        ),
                        "observed_at": observation.get(
                            "observed_at"
                        ),
                    }
                )

            products.append(
                {
                    "source": source,
                    "source_product_id": (
                        source_product_id
                    ),
                    "match_method": match.get(
                        "match_method"
                    ),
                    "match_confidence": match.get(
                        "match_confidence"
                    ),
                    "history": filtered_history,
                }
            )

        if not products:

            raise HTTPException(
                status_code=404,
                detail={
                    "error": (
                        "No competitive price history found"
                    ),
                    "canonical_product_id": (
                        canonical_product_id
                    ),
                },
            )

        service = PriceTrendService()

        trends = service.calculate_competitive_trends(
            products
        )

        source_order = {
            "AMAZON": 1,
            "WALMART": 2,
            "BESTBUY": 3,
        }

        trends.sort(
            key=lambda item: (
                source_order.get(
                    item.get("source"),
                    99,
                ),
                item.get("source", ""),
            )
        )

        latest_times = []

        for item in trends:

            history = item.get(
                "history",
                [],
            )

            if not history:
                continue

            latest_observed_at = history[-1].get(
                "observed_at"
            )

            if latest_observed_at:
                latest_times.append(
                    str(latest_observed_at)
                )

        last_updated = None

        if latest_times:
            last_updated = max(
                latest_times
            )

        return {
            "canonical_product_id": (
                canonical_product_id
            ),
            "reference_source": "AMAZON",
            "last_updated": last_updated,
            "products": trends,
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[API] GET "
            "/competitive-products/"
            "{canonical_product_id}/price-trends "
            "ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "Unable to calculate competitive "
                    "price trends"
                ),
                "type": type(e).__name__,
                "message": str(e),
            },
        )
