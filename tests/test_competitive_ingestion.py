from pricing_engine.connectors.amazon.connector import AmazonConnector
from pricing_engine.connectors.walmart.connector import WalmartConnector
from pricing_engine.connectors.bestbuy.connector import BestBuyConnector

from pricing_engine.intelligence.competitive_ingestion import (
    CompetitiveIngestionService,
)


def test_amazon_fixture_connector():
    connector = AmazonConnector(use_fixture=True)

    products = connector.fetch_products(
        query="sony",
        limit=10,
    )

    assert len(products) == 1

    product = products[0]

    assert product["source"] == "AMAZON"
    assert product["source_product_id"] == "FIXTURE-AMZ-001"
    assert product["brand"] == "Sony"
    assert product["model"] == "WH-1000XM5"
    assert product["gtin"] == "0194252777421"
    assert product["price"] == 349.0


def test_walmart_fixture_connector():
    connector = WalmartConnector(use_fixture=True)

    products = connector.fetch_products(
        query="sony",
        limit=10,
    )

    assert len(products) == 1

    product = products[0]

    assert product["source"] == "WALMART"
    assert product["source_product_id"] == "FIXTURE-WMT-001"
    assert product["brand"] == "Sony"
    assert product["gtin"] == "0194252777421"
    assert product["price"] == 339.0


def test_bestbuy_fixture_connector():
    connector = BestBuyConnector(use_fixture=True)

    products = connector.fetch_products(
        query="sony",
        limit=10,
    )

    assert len(products) == 1

    product = products[0]

    assert product["source"] == "BESTBUY"
    assert product["source_product_id"] == "FIXTURE-BBY-001"
    assert product["brand"] == "Sony"
    assert product["model"] == "WH-1000XM5"
    assert product["gtin"] == "0194252777421"
    assert product["price"] == 349.0


def test_competitive_ingestion_connectors():
    service = CompetitiveIngestionService(
        storage=None
    )

    connectors = service.get_connectors()

    assert len(connectors) == 3

    sources = [
        connector.get_source()
        for connector in connectors
    ]

    assert sources == [
        "AMAZON",
        "WALMART",
        "BESTBUY",
    ]


def test_competitive_ingestion_fetch_products():
    service = CompetitiveIngestionService(
        storage=None
    )

    products_by_source = service.fetch_products(
        query="sony",
        limit=10,
    )

    assert set(products_by_source.keys()) == {
        "AMAZON",
        "WALMART",
        "BESTBUY",
    }

    assert len(products_by_source["AMAZON"]) == 1
    assert len(products_by_source["WALMART"]) == 1
    assert len(products_by_source["BESTBUY"]) == 1

    amazon = products_by_source["AMAZON"][0]
    walmart = products_by_source["WALMART"][0]
    bestbuy = products_by_source["BESTBUY"][0]

    assert amazon["gtin"] == walmart["gtin"]
    assert walmart["gtin"] == bestbuy["gtin"]

    assert amazon["price"] == 349.0
    assert walmart["price"] == 339.0
    assert bestbuy["price"] == 349.0


def test_live_connector_requires_provider():
    amazon = AmazonConnector()

    try:
        amazon.fetch_products(
            query="sony",
            limit=10,
        )
    except NotImplementedError as exc:
        assert "Live Amazon collection" in str(exc)
    else:
        raise AssertionError(
            "Live Amazon collection should not be enabled yet"
        )