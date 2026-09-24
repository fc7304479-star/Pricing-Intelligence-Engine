from abc import ABC, abstractmethod
from datetime import datetime, timezone


class BaseProductConnector(ABC):
    """
    Common interface for all retailer product connectors.

    Every source connector must return products using the
    same normalized source-product structure.

    Examples of sources:
        AMAZON
        WALMART
        BESTBUY
        SHEIN
    """

    SOURCE = ""

    REQUIRED_FIELDS = [
        "source",
        "source_product_id",
        "product_name",
        "price",
        "currency",
        "availability",
        "observed_at",
    ]

    def __init__(self):
        if not self.SOURCE:
            raise ValueError(
                "Connector SOURCE must be defined"
            )

    # =========================================================
    # SOURCE NAME
    # =========================================================

    def get_source(self):
        """
        Return the uppercase source name.
        """

        return self.SOURCE.upper()

    # =========================================================
    # NORMALIZE PRODUCT
    # =========================================================

    def normalize_product(
        self,
        product,
    ):
        """
        Convert a connector product into the common
        source-product schema.
        """

        product = product or {}

        normalized = {
            "source": str(
                product.get("source")
                or self.SOURCE
                or ""
            ).strip().upper(),

            "source_product_id": str(
                product.get("source_product_id")
                or product.get("goods_id")
                or ""
            ).strip(),

            "product_name": str(
                product.get("product_name")
                or ""
            ).strip(),

            "brand": str(
                product.get("brand")
                or ""
            ).strip(),

            "model": str(
                product.get("model")
                or ""
            ).strip(),

            "gtin": str(
                product.get("gtin")
                or ""
            ).strip(),

            "sku": str(
                product.get("sku")
                or ""
            ).strip(),

            "price": product.get(
                "price"
            ),

            "original_price": product.get(
                "original_price"
            ),

            "discount": product.get(
                "discount"
            ),

            "currency": str(
                product.get("currency")
                or "USD"
            ).strip().upper(),

            "product_url": str(
                product.get("product_url")
                or ""
            ).strip(),

            "availability": str(
                product.get("availability")
                or "unknown"
            ).strip().lower(),

            "category": str(
                product.get("category")
                or "consumer_electronics"
            ).strip(),

            "observed_at": product.get(
                "observed_at"
            )
            or product.get("scraped_at")
            or datetime.now(
                timezone.utc
            ).isoformat(),
        }

        return normalized

    # =========================================================
    # VALIDATE PRODUCT
    # =========================================================

    def validate_product(
        self,
        product,
    ):
        """
        Validate the common source-product structure.

        Returns:

            {
                "valid": True,
                "errors": []
            }

        or:

            {
                "valid": False,
                "errors": [...]
            }
        """

        product = self.normalize_product(
            product
        )

        errors = []

        # -----------------------------------------------------
        # REQUIRED STRING FIELDS
        # -----------------------------------------------------

        if not product["source"]:
            errors.append(
                "source is required"
            )

        if not product["source_product_id"]:
            errors.append(
                "source_product_id is required"
            )

        if not product["product_name"]:
            errors.append(
                "product_name is required"
            )

        if not product["currency"]:
            errors.append(
                "currency is required"
            )

        if not product["availability"]:
            errors.append(
                "availability is required"
            )

        if not product["observed_at"]:
            errors.append(
                "observed_at is required"
            )

        # -----------------------------------------------------
        # PRICE VALIDATION
        # -----------------------------------------------------

        price = product["price"]

        if price is not None:

            try:
                price = float(price)

                if price < 0:
                    errors.append(
                        "price cannot be negative"
                    )

            except (
                TypeError,
                ValueError,
            ):
                errors.append(
                    "price must be numeric or None"
                )

        # -----------------------------------------------------
        # SOURCE VALIDATION
        # -----------------------------------------------------

        if (
            product["source"]
            != self.SOURCE.upper()
        ):
            errors.append(
                "source does not match connector SOURCE"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    # =========================================================
    # PREPARE PRODUCT
    # =========================================================

    def prepare_product(
        self,
        product,
    ):
        """
        Normalize and validate a source product.

        Raises ValueError when validation fails.

        Returns the clean common product dictionary.
        """

        normalized = self.normalize_product(
            product
        )

        validation = self.validate_product(
            normalized
        )

        if not validation["valid"]:
            raise ValueError(
                "Invalid product: "
                + "; ".join(
                    validation["errors"]
                )
            )

        return normalized

    # =========================================================
    # FETCH PRODUCTS
    # =========================================================

    @abstractmethod
    def fetch_products(
        self,
        **kwargs,
    ):
        """
        Fetch products from the source.

        Every retailer connector must implement this method.

        Returns:
            list[dict]
        """

        raise NotImplementedError

    # =========================================================
    # FETCH ONE PRODUCT
    # =========================================================

    @abstractmethod
    def fetch_product(
        self,
        source_product_id,
        **kwargs,
    ):
        """
        Fetch one product from the source.

        Every retailer connector must implement this method.

        Returns:
            dict
        """

        raise NotImplementedError