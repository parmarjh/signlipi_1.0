"""Brain-Computer Interface (BCI) module.

Goals:
  * Provide a vendor-neutral interface for decoding intent from EEG samples.
  * Ship a lightweight, offline, CPU-only classifier that works out of the box
    using band-power features (alpha / beta / theta).
  * Expose REST endpoints to classify a buffer of samples or ingest a live
    stream later.

Real hardware integrations (OpenBCI, Muse, Neurosity, BrainFlow) can be
plugged into `StreamSource` implementations without changing the API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from scipy.signal import welch


# Default vocabulary — each intent maps to a text token the UI can append
DEFAULT_INTENTS: List[str] = [
    "yes",
    "no",
    "left",
    "right",
    "select",
    "cancel",
    "hello",
    "help",
]


BANDS: Dict[str, Tuple[float, float]] = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}


@dataclass
class BCIResult:
    intent: str
    confidence: float
    features: Dict[str, float]


def band_powers(signal: np.ndarray, fs: float) -> Dict[str, float]:
    """Compute average power in each EEG band using Welch's method."""
    if signal.ndim == 2:
        signal = signal.mean(axis=0)  # average across channels
    nperseg = min(256, len(signal))
    freqs, psd = welch(signal, fs=fs, nperseg=nperseg)
    out: Dict[str, float] = {}
    for name, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        out[name] = float(np.trapz(psd[mask], freqs[mask])) if mask.any() else 0.0
    return out


class BandPowerClassifier:
    """Heuristic classifier mapping dominant band → intent.

    This is designed so the full pipeline is runnable with mock signals
    today, and so a trained LDA/SVM model can drop in later via `load`.
    """

    def __init__(self, intents: List[str] | None = None) -> None:
        self.intents = intents or DEFAULT_INTENTS

    def predict(self, signal: np.ndarray, fs: float = 250.0) -> BCIResult:
        bp = band_powers(signal, fs)
        total = sum(bp.values()) + 1e-9
        norm = {k: v / total for k, v in bp.items()}

        # Heuristic mapping — alpha dominant → relaxed "yes";
        # beta dominant → focused "select"; theta → "no"; gamma → "help"
        if norm["alpha"] > 0.35:
            intent, conf = "yes", norm["alpha"]
        elif norm["beta"] > 0.35:
            intent, conf = "select", norm["beta"]
        elif norm["theta"] > 0.3:
            intent, conf = "no", norm["theta"]
        elif norm["gamma"] > 0.2:
            intent, conf = "help", norm["gamma"]
        else:
            # fall back to argmax among known intents
            dominant = max(norm, key=norm.get)
            intent = {
                "delta": "cancel",
                "theta": "no",
                "alpha": "yes",
                "beta": "select",
                "gamma": "help",
            }.get(dominant, "yes")
            conf = norm[dominant]
        return BCIResult(intent=intent, confidence=float(conf), features=norm)


_classifier = BandPowerClassifier()


def classify(samples: List[List[float]] | np.ndarray, fs: float = 250.0) -> BCIResult:
    arr = np.array(samples, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr[None, :]
    return _classifier.predict(arr, fs)


def synthesize_mock(kind: str = "alpha", seconds: float = 2.0, fs: float = 250.0) -> List[float]:
    """Generate a mock EEG-like signal for testing — a sine wave in the
    requested band plus pink-ish noise."""
    t = np.linspace(0, seconds, int(seconds * fs), endpoint=False)
    freq_map = {"delta": 2, "theta": 6, "alpha": 10, "beta": 20, "gamma": 35}
    f = freq_map.get(kind, 10)
    sig = np.sin(2 * np.pi * f * t)
    noise = np.random.randn(len(t)) * 0.3
    return (sig + noise).astype(np.float32).tolist()
