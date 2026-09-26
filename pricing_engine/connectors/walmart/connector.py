from pricing_engine.connectors.base_connector import (
    BaseProductConnector,
)
from pricing_engine.connectors.providers.walmart_provider import (
    WalmartProvider,
)


class WalmartConnector(BaseProductConnector):
    """
    Walmart product connector.

    The connector owns the common product contract while
    the provider owns product acquisition.

    Current provider:
        WalmartProvider (fixture-backed)

    A live official/API provider can be introduced later
    without changing the connector contract.
    """

    SOURCE = "WALMART"

    def __init__(
        self,
        use_fixture=False,
        provider=None,
    ):
        super().__init__()

        self.use_fixture = bool(use_fixture)

        if provider is not None:
            self.provider = provider
        elif self.use_fixture:
            self.provider = WalmartProvider()
        else:
            self.provider = None

    def fetch_products(
        self,
        query=None,
        limit=10,
        **kwargs,
    ):
        if self.provider is None:
            raise NotImplementedError(
                "Live Walmart collection is not enabled yet"
            )

        products = self.provider.fetch_products(
            query=query,
            limit=limit,
            **kwargs,
        )

        return [
            self.prepare_product(product)
            for product in products
        ]

    def fetch_product(
        self,
        source_product_id,
        **kwargs,
    ):
        source_product_id = str(
            source_product_id or ""
        ).strip()

        if not source_product_id:
            raise ValueError(
                "source_product_id is required"
            )

        if self.provider is None:
            raise NotImplementedError(
                "Live Walmart collection is not enabled yet"
            )

        product = self.provider.fetch_product(
            source_product_id=source_product_id,
            **kwargs,
        )

        if product is None:
            return None

        return self.prepare_product(product)