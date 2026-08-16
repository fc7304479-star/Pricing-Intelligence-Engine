from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pricing_engine.api.routes import router


app = FastAPI(
    title="Pricing Intelligence API"
)


# ---------------------------------------
# CORS
# ---------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Local frontend
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        # Vercel production
        "https://pricing-intelligence-dashboard-eta.vercel.app",

        # Vercel Git/Main deployment
        "https://pricing-intelligence-dashboard-git-main-fahad-ab15.vercel.app",

        # Current Vercel preview
        "https://pricing-intelligence-dashboard-hx3kyy2fh-fahad-ab15.vercel.app",
    ],

    # Allow Vercel preview deployments too
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------
# Routes
# ---------------------------------------

app.include_router(router)


# ---------------------------------------
# Health
# ---------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }