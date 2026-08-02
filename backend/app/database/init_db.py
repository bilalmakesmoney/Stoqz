# pyrefly: ignore [missing-import]
from app.database.database import Base, engine

# Import all models so SQLAlchemy knows they exist
# pyrefly: ignore [missing-import]
from app.database.models import Product, SaleRecord, PredictionRecord

Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")