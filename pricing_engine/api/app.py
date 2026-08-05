from fastapi import FastAPI

from pricing_engine.api.routes import router

app = FastAPI(

    title="Pricing Intelligence Engine",

    description="AI Powered Pricing Intelligence Platform",

    version="1.0.0"

)

app.include_router(router)