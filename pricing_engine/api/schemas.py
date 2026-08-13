from pydantic import BaseModel


class Product(BaseModel):
    title: str
    price: float
    currency: str = "USD"
    source: str = ""
    url: str = ""