from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pricing_engine.api.routes import router


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Pricing Intelligence Engine",
    version="1.0.0",
    description="Pricing Intelligence API powered by FastAPI and ClickHouse",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Pricing Intelligence Engine API",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }