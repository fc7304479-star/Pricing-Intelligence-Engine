from pricing_engine.connectors.providers.fixture_provider import (
    FixtureProductProvider,
)


class AmazonProvider(FixtureProductProvider):
    """
    Amazon acquisition provider.

    Currently uses deterministic fixture data.
    A live official/API implementation can replace the
    acquisition logic later without changing the connector
    or intelligence layers.
    """

    SOURCE = "AMAZON"

    def __init__(self):
        super().__init__(source=self.SOURCE)