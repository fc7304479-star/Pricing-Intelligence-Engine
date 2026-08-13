from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pricing_engine.api.routes import router

app = FastAPI(
    title="Pricing Intelligence Engine",
    version="1.0.0"
)

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(router)