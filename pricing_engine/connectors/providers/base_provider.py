from abc import ABC, abstractmethod


class BaseProductProvider(ABC):
    """
    Common provider interface for retailer product acquisition.

    A provider is responsible only for obtaining source product data.

    It does NOT handle:
        - product matching
        - canonical product creation
        - historical storage
        - price comparison
        - pricing signals

    Those responsibilities remain in the existing intelligence
    and storage layers.
    """

    SOURCE = ""

    def __init__(self):
        if not self.SOURCE:
            raise ValueError(
                "Provider SOURCE must be defined"
            )

    def get_source(self):
        """
        Return the uppercase source name.
        """
        return self.SOURCE.upper()

    @abstractmethod
    def fetch_products(
        self,
        query=None,
        limit=10,
        **kwargs,
    ):
        """
        Fetch multiple products from the source.

        Returns:
            list[dict]
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_product(
        self,
        source_product_id,
        **kwargs,
    ):
        """
        Fetch one product by source-specific product ID.

        Returns:
            dict | None
        """
        raise NotImplementedError