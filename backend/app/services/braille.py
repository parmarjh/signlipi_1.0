"""Grade-1 English Braille <-> text translator, plus Unicode dot rendering.

Self-contained: no external `liblouis` dependency required. For full Grade-2
contractions, integrate `pylouis` / `liblouis` later.
"""
from __future__ import annotations

from typing import Dict, List

# Unicode Braille block: U+2800 .. U+28FF. Each cell is a 2x4 dot matrix:
#   1 4
#   2 5
#   3 6
#   7 8  (8-dot extension)
# Dot n contributes 1 << (n-1) to the offset from U+2800.

# Grade-1 English letters (dots 1-6 only)
LETTER_DOTS: Dict[str, List[int]] = {
    "a": [1],
    "b": [1, 2],
    "c": [1, 4],
    "d": [1, 4, 5],
    "e": [1, 5],
    "f": [1, 2, 4],
    "g": [1, 2, 4, 5],
    "h": [1, 2, 5],
    "i": [2, 4],
    "j": [2, 4, 5],
    "k": [1, 3],
    "l": [1, 2, 3],
    "m": [1, 3, 4],
    "n": [1, 3, 4, 5],
    "o": [1, 3, 5],
    "p": [1, 2, 3, 4],
    "q": [1, 2, 3, 4, 5],
    "r": [1, 2, 3, 5],
    "s": [2, 3, 4],
    "t": [2, 3, 4, 5],
    "u": [1, 3, 6],
    "v": [1, 2, 3, 6],
    "w": [2, 4, 5, 6],
    "x": [1, 3, 4, 6],
    "y": [1, 3, 4, 5, 6],
    "z": [1, 3, 5, 6],
}

# Digits (preceded by the number indicator ⠼ = dots 3,4,5,6)
DIGIT_DOTS: Dict[str, List[int]] = {
    "1": [1],
    "2": [1, 2],
    "3": [1, 4],
    "4": [1, 4, 5],
    "5": [1, 5],
    "6": [1, 2, 4],
    "7": [1, 2, 4, 5],
    "8": [1, 2, 5],
    "9": [2, 4],
    "0": [2, 4, 5],
}

PUNCT_DOTS: Dict[str, List[int]] = {
    ",": [2],
    ";": [2, 3],
    ":": [2, 5],
    ".": [2, 5, 6],
    "?": [2, 3, 6],
    "!": [2, 3, 5],
    "'": [3],
    "-": [3, 6],
    "(": [1, 2, 3, 5, 6],
    ")": [2, 3, 4, 5, 6],
    '"': [2, 3, 6],
    "/": [3, 4],
}

NUMBER_INDICATOR = [3, 4, 5, 6]   # ⠼
CAPITAL_INDICATOR = [6]           # ⠠


def _dots_to_char(dots: List[int]) -> str:
    offset = 0
    for d in dots:
        offset |= 1 << (d - 1)
    return chr(0x2800 + offset)


def _char_to_dots(ch: str) -> List[int]:
    code = ord(ch) - 0x2800
    return [i + 1 for i in range(8) if code & (1 << i)]


def text_to_braille(text: str) -> str:
    """Convert plain text to Unicode Braille (Grade-1, English)."""
    out: List[str] = []
    in_number = False
    for ch in text:
        if ch.isspace():
            out.append(" ")
            in_number = False
            continue
        if ch.isdigit():
            if not in_number:
                out.append(_dots_to_char(NUMBER_INDICATOR))
                in_number = True
            out.append(_dots_to_char(DIGIT_DOTS[ch]))
            continue
        in_number = False
        if ch.isupper():
            out.append(_dots_to_char(CAPITAL_INDICATOR))
            lower = ch.lower()
            if lower in LETTER_DOTS:
                out.append(_dots_to_char(LETTER_DOTS[lower]))
            continue
        if ch in LETTER_DOTS:
            out.append(_dots_to_char(LETTER_DOTS[ch]))
        elif ch in PUNCT_DOTS:
            out.append(_dots_to_char(PUNCT_DOTS[ch]))
        else:
            out.append(ch)  # passthrough for unsupported chars
    return "".join(out)


def braille_to_text(braille: str) -> str:
    """Inverse mapping. Ignores unknown cells."""
    # Build reverse tables
    rev_letters = {tuple(v): k for k, v in LETTER_DOTS.items()}
    rev_digits = {tuple(v): k for k, v in DIGIT_DOTS.items()}
    rev_punct = {tuple(v): k for k, v in PUNCT_DOTS.items()}

    out: List[str] = []
    cap_next = False
    number_mode = False
    for ch in braille:
        if ch == " ":
            out.append(" ")
            number_mode = False
            cap_next = False
            continue
        if 0x2800 <= ord(ch) <= 0x28FF:
            dots = tuple(_char_to_dots(ch))
            if dots == tuple(CAPITAL_INDICATOR):
                cap_next = True
                continue
            if dots == tuple(NUMBER_INDICATOR):
                number_mode = True
                continue
            if number_mode and dots in rev_digits:
                out.append(rev_digits[dots])
                continue
            if dots in rev_letters:
                letter = rev_letters[dots]
                out.append(letter.upper() if cap_next else letter)
                cap_next = False
                continue
            if dots in rev_punct:
                out.append(rev_punct[dots])
                number_mode = False
                continue
        else:
            out.append(ch)
    return "".join(out)


def dots_grid(text: str) -> List[List[List[int]]]:
    """Return a 2x4 (cols x rows) dot grid per cell — handy for UI rendering."""
    grids: List[List[List[int]]] = []
    braille = text_to_braille(text)
    for ch in braille:
        if 0x2800 <= ord(ch) <= 0x28FF:
            dots = set(_char_to_dots(ch))
            grid = [
                [1 if 1 in dots else 0, 1 if 4 in dots else 0],
                [1 if 2 in dots else 0, 1 if 5 in dots else 0],
                [1 if 3 in dots else 0, 1 if 6 in dots else 0],
                [1 if 7 in dots else 0, 1 if 8 in dots else 0],
            ]
            grids.append(grid)
        elif ch == " ":
            grids.append([[0, 0]] * 4)
    return grids
