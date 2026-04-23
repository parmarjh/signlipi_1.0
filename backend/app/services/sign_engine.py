"""Sign language recognition engine.

Uses MediaPipe Hands to extract 21 hand landmarks, then a rule-based
classifier over normalized finger-tip geometry to detect A-Z letters for
ASL and a small set of ISL one/two-handed signs. This is intentionally
dependency-light so it runs fully offline on CPU.

For production accuracy, swap `RuleSignClassifier` with a trained
scikit-learn / torch model loaded from `models/`.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:  # pragma: no cover
    mp = None  # type: ignore


# --- Landmark helpers -------------------------------------------------------

FINGER_TIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
FINGER_PIPS = {"thumb": 3, "index": 6, "middle": 10, "ring": 14, "pinky": 18}
FINGER_MCPS = {"thumb": 2, "index": 5, "middle": 9, "ring": 13, "pinky": 17}


@dataclass
class HandSnapshot:
    landmarks: np.ndarray  # (21, 3)
    handedness: str  # "Left" | "Right"


def _finger_states(lm: np.ndarray) -> Dict[str, bool]:
    """Return which fingers are extended (True) vs folded."""
    out: Dict[str, bool] = {}
    # Thumb: compare x of tip vs ip, using handedness-agnostic absolute distance
    out["thumb"] = abs(lm[4, 0] - lm[2, 0]) > abs(lm[3, 0] - lm[2, 0]) * 1.1
    # Other fingers: tip.y < pip.y (image coords: smaller y = higher)
    for name in ["index", "middle", "ring", "pinky"]:
        tip = FINGER_TIPS[name]
        pip = FINGER_PIPS[name]
        out[name] = lm[tip, 1] < lm[pip, 1] - 0.02
    return out


def _normalize(lm: np.ndarray) -> np.ndarray:
    """Translate to wrist, scale by palm size."""
    wrist = lm[0]
    centered = lm - wrist
    palm = np.linalg.norm(lm[9] - lm[0]) + 1e-6
    return centered / palm


# --- Rule-based classifier --------------------------------------------------

class RuleSignClassifier:
    """Very small rule-based recognizer for demo purposes.

    Supports ASL letters: A, B, C, D, I, L, O, V, W, Y and "space".
    Supports ISL signs: "hello" (open palm wave), "yes", "no", "ok".
    """

    def __init__(self, mode: str = "ASL") -> None:
        self.mode = mode.upper()

    def set_mode(self, mode: str) -> None:
        self.mode = mode.upper()

    def predict(self, hands: List[HandSnapshot]) -> Tuple[str, float]:
        if not hands:
            return "", 0.0
        if self.mode == "ISL":
            return self._predict_isl(hands)
        return self._predict_asl(hands[0])

    # ---- ASL ----
    def _predict_asl(self, hand: HandSnapshot) -> Tuple[str, float]:
        lm = _normalize(hand.landmarks)
        st = _finger_states(hand.landmarks)

        # Pattern table (thumb, index, middle, ring, pinky)
        patterns = {
            "A": (False, False, False, False, False),
            "B": (False, True, True, True, True),
            "C": (True, True, True, True, True),   # curved — fallback
            "D": (False, True, False, False, False),
            "I": (False, False, False, False, True),
            "L": (True, True, False, False, False),
            "O": (False, False, False, False, False),  # disambiguated below
            "V": (False, True, True, False, False),
            "W": (False, True, True, True, False),
            "Y": (True, False, False, False, True),
        }
        key = (st["thumb"], st["index"], st["middle"], st["ring"], st["pinky"])
        best = None
        for letter, patt in patterns.items():
            if patt == key:
                best = letter
                break

        # Disambiguate "O" vs "A": in O the index tip is close to thumb tip
        if best == "A":
            d = np.linalg.norm(lm[4, :2] - lm[8, :2])
            if d < 0.35:
                best = "O"

        # Disambiguate "C" — curled fingers, thumb out, tip-pip distances medium
        if best is None:
            curls = [
                np.linalg.norm(lm[FINGER_TIPS[f], :2] - lm[FINGER_PIPS[f], :2])
                for f in ("index", "middle", "ring", "pinky")
            ]
            if 0.15 < np.mean(curls) < 0.45:
                best = "C"

        if best is None:
            return "", 0.2
        return best, 0.85

    # ---- ISL (mostly two-handed) ----
    def _predict_isl(self, hands: List[HandSnapshot]) -> Tuple[str, float]:
        if len(hands) == 1:
            st = _finger_states(hands[0].landmarks)
            if all(st.values()):
                return "hello", 0.75
            if st["thumb"] and not any(st[f] for f in ("index", "middle", "ring", "pinky")):
                return "yes", 0.8
            if st["index"] and st["middle"] and not st["ring"] and not st["pinky"]:
                return "peace", 0.7
            if not any(st.values()):
                return "no", 0.6
            return "", 0.3

        # Two hands — distance-based heuristics
        a = _normalize(hands[0].landmarks)
        b = _normalize(hands[1].landmarks)
        palm_dist = np.linalg.norm(a[9] - b[9])
        if palm_dist < 0.8:
            return "namaste", 0.8
        return "friend", 0.55


# --- MediaPipe wrapper ------------------------------------------------------

class SignEngine:
    def __init__(self, max_hands: int = 2, detection_conf: float = 0.6) -> None:
        if mp is None:
            raise RuntimeError("mediapipe is not installed")
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=0.5,
        )
        self.classifier = RuleSignClassifier(mode="ASL")

    def close(self) -> None:
        self._hands.close()

    def set_mode(self, mode: str) -> None:
        self.classifier.set_mode(mode)

    def process_bgr(self, frame_bgr: np.ndarray) -> Dict:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self._hands.process(rgb)
        hands: List[HandSnapshot] = []
        landmark_payload: List[List[List[float]]] = []

        if res.multi_hand_landmarks:
            for i, hand_lms in enumerate(res.multi_hand_landmarks):
                arr = np.array([[p.x, p.y, p.z] for p in hand_lms.landmark], dtype=np.float32)
                handedness = "Right"
                if res.multi_handedness and i < len(res.multi_handedness):
                    handedness = res.multi_handedness[i].classification[0].label
                hands.append(HandSnapshot(landmarks=arr, handedness=handedness))
                landmark_payload.append(arr.tolist())

        label, conf = self.classifier.predict(hands)
        return {
            "label": label,
            "confidence": float(conf),
            "num_hands": len(hands),
            "landmarks": landmark_payload,
            "mode": self.classifier.mode,
        }

    def process_b64(self, b64_data: str) -> Dict:
        """Decode base64 JPEG/PNG and classify."""
        if b64_data.startswith("data:"):
            b64_data = b64_data.split(",", 1)[1]
        raw = base64.b64decode(b64_data)
        arr = np.frombuffer(raw, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"error": "invalid image", "label": "", "confidence": 0.0}
        return self.process_bgr(frame)


# Global singleton (cheap to keep one instance)
_engine: Optional[SignEngine] = None


def get_sign_engine() -> SignEngine:
    global _engine
    if _engine is None:
        _engine = SignEngine()
    return _engine
