"""FastAPI entrypoint for Sign Language + Brain Lipi Translator."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import braille, bci, genai, health, sign_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up services (e.g. load models) on startup if needed
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SignLipi — Sign Language & Brain Lipi Translator",
        description=(
            "Open-source local-host translator that converts sign language (ASL + ISL) "
            "and brain-lipi (Braille + BCI) to text, with a local GenAI (Ollama) layer."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(sign_ws.router, tags=["sign"])
    app.include_router(braille.router, prefix="/api/braille", tags=["braille"])
    app.include_router(bci.router, prefix="/api/bci", tags=["bci"])
    app.include_router(genai.router, prefix="/api/genai", tags=["genai"])

    @app.get("/")
    async def root():
        return JSONResponse(
            {
                "name": "SignLipi",
                "status": "ok",
                "docs": "/docs",
                "endpoints": [
                    "/api/health",
                    "/ws/sign",
                    "/api/braille/encode",
                    "/api/braille/decode",
                    "/api/bci/classify",
                    "/api/genai/chat",
                    "/api/genai/correct",
                ],
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
