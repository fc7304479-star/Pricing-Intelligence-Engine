import re
import unicodedata


class ProductNormalizer:
    """
    Normalizes product identity fields before cross-source matching.

    This class does not decide whether two products are the same.
    It only prepares comparable identity values.
    """

    @staticmethod
    def normalize_text(value):
        """
        Normalize general product text.

        Example:
            "Sony WH-1000XM5 Wireless Headphones!"
            ->
            "sony wh 1000xm5 wireless headphones"
        """

        if value is None:
            return ""

        value = str(value).strip()

        if not value:
            return ""

        value = unicodedata.normalize(
            "NFKD",
            value
        )

        value = value.encode(
            "ascii",
            "ignore"
        ).decode(
            "ascii"
        )

        value = value.lower()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    @staticmethod
    def normalize_brand(value):
        """
        Normalize brand name.
        """

        return ProductNormalizer.normalize_text(
            value
        )

    @staticmethod
    def normalize_model(value):
        """
        Normalize manufacturer model / MPN.

        Keeps letters and numbers while removing
        separators such as -, / and spaces.
        """

        if value is None:
            return ""

        value = str(value).strip()

        if not value:
            return ""

        value = unicodedata.normalize(
            "NFKD",
            value
        )

        value = value.encode(
            "ascii",
            "ignore"
        ).decode(
            "ascii"
        )

        value = value.lower()

        value = re.sub(
            r"[^a-z0-9]",
            "",
            value
        )

        return value

    @staticmethod
    def normalize_gtin(value):
        """
        Normalize GTIN / UPC / EAN.

        Only numeric characters are retained.
        """

        if value is None:
            return ""

        value = str(value).strip()

        if not value:
            return ""

        value = re.sub(
            r"[^0-9]",
            "",
            value
        )

        return value

    @staticmethod
    def normalize_sku(value):
        """
        Normalize source SKU.
        """

        if value is None:
            return ""

        value = str(value).strip()

        if not value:
            return ""

        value = unicodedata.normalize(
            "NFKD",
            value
        )

        value = value.encode(
            "ascii",
            "ignore"
        ).decode(
            "ascii"
        )

        value = value.lower()

        value = re.sub(
            r"[^a-z0-9]",
            "",
            value
        )

        return value

    @classmethod
    def normalize_product(cls, product):
        """
        Normalize a complete product dictionary.

        Expected fields may include:
            product_name
            brand
            model
            gtin
            sku
            source
            source_product_id
        """

        product = product or {}

        return {
            "source": str(
                product.get("source") or ""
            ).strip().upper(),

            "source_product_id": str(
                product.get("source_product_id")
                or product.get("goods_id")
                or ""
            ).strip(),

            "product_name": str(
                product.get("product_name") or ""
            ).strip(),

            "normalized_name": cls.normalize_text(
                product.get("product_name")
            ),

            "brand": str(
                product.get("brand") or ""
            ).strip(),

            "normalized_brand": cls.normalize_brand(
                product.get("brand")
            ),

            "model": str(
                product.get("model") or ""
            ).strip(),

            "normalized_model": cls.normalize_model(
                product.get("model")
            ),

            "gtin": str(
                product.get("gtin") or ""
            ).strip(),

            "normalized_gtin": cls.normalize_gtin(
                product.get("gtin")
            ),

            "sku": str(
                product.get("sku") or ""
            ).strip(),

            "normalized_sku": cls.normalize_sku(
                product.get("sku")
            ),
        }