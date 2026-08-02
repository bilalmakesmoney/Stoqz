from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

# pyrefly: ignore [missing-import]
from app.database.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)


class SaleRecord(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    sale_date = Column(Date, nullable=False)

    product_name = Column(String, nullable=False)

    sku = Column(String, nullable=True)

    category = Column(String, nullable=True)

    quantity_sold = Column(Integer, nullable=False)

    current_stock = Column(Integer, nullable=True)

    unit_cost = Column(Float, nullable=True)

    reorder_point = Column(Integer, nullable=True)


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String, nullable=False)

    sku = Column(String, nullable=True)

    category = Column(String, nullable=True)

    predicted_demand = Column(Float, nullable=False)

    recommended_order = Column(Integer, nullable=False)

    current_stock = Column(Integer, nullable=False)

    confidence = Column(Float, nullable=False)

    prediction_date = Column(Date, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    explanation = Column(String, nullable=True)


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)