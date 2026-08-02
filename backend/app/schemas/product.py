# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    category: str
    unit_price: float
    shelf_life_days: int