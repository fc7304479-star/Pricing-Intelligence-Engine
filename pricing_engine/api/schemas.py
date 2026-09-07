from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    goods_id: str
    product_name: str
    product_url: str = ""
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount: Optional[float] = None
    source: str = "SHEIN"
    currency: str = "USD"
    availability: str = "unknown"
    scraped_at: str = ""