# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class Inventory(BaseModel):
    product_id: int
    current_stock: int