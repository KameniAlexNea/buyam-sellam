"""Buyam-Sellam FastAPI application entry point."""

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ksell.strategy import ALL_STRATEGIES
from app.routes import router

app = FastAPI(
    title="Buyam-Sellam API",
    description="REST API for the Buyam-Sellam trading board game.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/strategies", tags=["strategies"])
def list_strategies():
    """List available AI bot strategies for the frontend."""
    return [
        {"name": name, "label": cls.label, "description": cls.description}
        for name, cls in sorted(ALL_STRATEGIES.items())
    ]


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return actual traceback on 500 errors for debugging."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        },
    )


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
