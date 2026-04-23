from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.bci import classify, synthesize_mock

router = APIRouter()


class BCIRequest(BaseModel):
    samples: List[List[float]] | List[float]
    fs: float = 250.0


class MockRequest(BaseModel):
    kind: str = "alpha"
    seconds: float = 2.0
    fs: float = 250.0


@router.post("/classify")
async def classify_samples(req: BCIRequest):
    r = classify(req.samples, req.fs)
    return {"intent": r.intent, "confidence": r.confidence, "features": r.features}


@router.post("/mock")
async def mock_signal(req: MockRequest):
    sig = synthesize_mock(req.kind, req.seconds, req.fs)
    r = classify([sig], req.fs)
    return {
        "intent": r.intent,
        "confidence": r.confidence,
        "features": r.features,
        "sample_count": len(sig),
    }
