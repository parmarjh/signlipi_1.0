from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import genai as genai_service

router = APIRouter()


class TokensIn(BaseModel):
    tokens: List[str]
    mode: str = "ASL"


class TextIn(BaseModel):
    text: str


class ChatIn(BaseModel):
    messages: List[Dict[str, str]]


@router.post("/compose")
async def compose(body: TokensIn):
    try:
        sentence = await genai_service.sign_to_sentence(body.tokens, body.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"sentence": sentence, "tokens": body.tokens, "mode": body.mode}


@router.post("/correct")
async def correct(body: TextIn):
    try:
        corrected = await genai_service.correct_text(body.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"input": body.text, "output": corrected}


@router.post("/chat")
async def chat(body: ChatIn):
    try:
        reply = await genai_service.chat(body.messages)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"reply": reply}
