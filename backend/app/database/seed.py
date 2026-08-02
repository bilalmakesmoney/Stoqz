# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

# pyrefly: ignore [missing-import]
from app.database.database import SessionLocal
# pyrefly: ignore [missing-import]
from app.database.models import Product

db: Session = SessionLocal()

products = [
    Product(
        name="Milk",
        category="Dairy",
        unit_price=30,
        shelf_life_days=7,
    ),
    Product(
        name="Bread",
        category="Bakery",
        unit_price=40,
        shelf_life_days=3,
    ),
    Product(
        name="Eggs",
        category="Dairy",
        unit_price=7,
        shelf_life_days=14,
    ),
]

db.add_all(products)
db.commit()

print("Products inserted successfully!")

db.close()