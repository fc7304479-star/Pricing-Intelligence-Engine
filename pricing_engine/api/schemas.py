from pydantic import BaseModel


class Product(BaseModel):

    title: str
    price: str
    currency: str
    source: str
    url: str