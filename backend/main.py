# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]
from app.api.prediction import router as prediction_router
# pyrefly: ignore [missing-import]
from app.api.upload import router as upload_router

# pyrefly: ignore [missing-import]
from app.api.dashboard import router as dashboard_router
# pyrefly: ignore [missing-import]
from app.api.analytics import router as analytics_router 
# pyrefly: ignore [missing-import]
from app.api.recommendations import router as recommendations_router   

# pyrefly: ignore [missing-import]
from app.api.insights import router as insights_router

# pyrefly: ignore [missing-import]
from app.database.database import engine, Base
# pyrefly: ignore [missing-import]
import app.database.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RetailPilot AI",
    description="AI-powered inventory demand forecasting and smart order recommendation system.",
    version="1.0.0",
)

# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Routers
# -------------------------

app.include_router(upload_router)
app.include_router(prediction_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(recommendations_router)
app.include_router(insights_router)

# -------------------------
# Root
# -------------------------


@app.get("/")
def root():
    return {
        "application": "RetailPilot AI",
        "status": "Running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "RetailPilot AI Backend is running."
    }