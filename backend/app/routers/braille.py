from fastapi import APIRouter
from pydantic import BaseModel

from app.services.braille import text_to_braille, braille_to_text, dots_grid

router = APIRouter()


class EncodeIn(BaseModel):
    text: str


class DecodeIn(BaseModel):
    braille: str


@router.post("/encode")
async def encode(body: EncodeIn):
    return {
        "text": body.text,
        "braille": text_to_braille(body.text),
        "grid": dots_grid(body.text),
    }


@router.post("/decode")
async def decode(body: DecodeIn):
    return {"braille": body.braille, "text": braille_to_text(body.braille)}
