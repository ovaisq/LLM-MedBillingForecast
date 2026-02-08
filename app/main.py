"""FastAPI application for medical billing forecasting."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as api_router

app = FastAPI(
    title="Billing Forecast GPT",
    description="Medical Billing Forecasting using LLMs",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Application startup initialization."""
    logging.info("Starting Billing Forecast GPT API")
    logging.info("Loading configuration...")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": "Billing Forecast GPT API",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
    }


@app.get("/health", include_in_schema=False)
@app.get("/healthcheck", include_in_schema=False)
@app.get("/v1/health", include_in_schema=False)
@app.get("/v1/healthcheck", include_in_schema=False)
async def health_check_fallback():
    """Fallback health check endpoints."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
    )
