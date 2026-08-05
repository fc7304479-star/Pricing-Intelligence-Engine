from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceRecord:

    title: str

    url: str

    price: str

    timestamp: datetime

    source: str = "DemoShop"

    currency: str = "USD"