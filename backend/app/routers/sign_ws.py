"""WebSocket + REST routes for real-time sign language recognition."""
from __future__ import annotations

import json
import time
from typing import List

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from app.services.sign_engine import get_sign_engine

router = APIRouter()


class SignFrame(BaseModel):
    image_b64: str
    mode: str = "ASL"


class SignResult(BaseModel):
    label: str
    confidence: float
    num_hands: int
    mode: str


@router.post("/api/sign/frame", response_model=SignResult)
async def sign_frame(payload: SignFrame):
    engine = get_sign_engine()
    engine.set_mode(payload.mode)
    try:
        result = engine.process_b64(payload.image_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return SignResult(**{k: result[k] for k in ("label", "confidence", "num_hands", "mode")})


@router.post("/api/sign/upload")
async def sign_upload(file: UploadFile = File(...), mode: str = "ASL"):
    import cv2, numpy as np
    data = await file.read()
    arr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="invalid image")
    engine = get_sign_engine()
    engine.set_mode(mode)
    return engine.process_bgr(frame)


@router.websocket("/ws/sign")
async def sign_ws(ws: WebSocket):
    """Bidirectional stream — client sends JSON frames, server returns predictions.

    Client message schema:
        { "image_b64": "...", "mode": "ASL" | "ISL" }
    Server message schema:
        { "label", "confidence", "num_hands", "mode", "landmarks", "ts" }
    """
    await ws.accept()
    engine = get_sign_engine()
    buffer: List[str] = []
    last_emit = ""
    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                await ws.send_json({"error": "invalid json"})
                continue

            if data.get("type") == "reset":
                buffer.clear()
                await ws.send_json({"type": "reset_ack", "sentence": ""})
                continue

            mode = data.get("mode", "ASL")
            engine.set_mode(mode)
            image_b64 = data.get("image_b64", "")
            if not image_b64:
                continue
            result = engine.process_b64(image_b64)
            result["ts"] = time.time()

            # Debounce: only append to sentence buffer when label stabilises
            label = result.get("label") or ""
            if label and label != last_emit and result.get("confidence", 0) >= 0.7:
                buffer.append(label)
                last_emit = label
            result["sentence"] = "".join(buffer) if mode.upper() == "ASL" else " ".join(buffer)
            await ws.send_json(result)
    except WebSocketDisconnect:
        return
