"""
Vibration signal analysis for predictive maintenance — numpy only (no new deps).

Implements the standard rotating-machinery toolkit:
  - time-domain features: RMS, peak, peak-to-peak, crest factor, kurtosis, skewness
  - FFT amplitude spectrum (Hanning-windowed, single-sided)
  - envelope (Hilbert) spectrum — demodulates high-freq resonance to reveal bearing defects
  - bearing characteristic frequencies (BPFO/BPFI/BSF/FTF) from geometry
  - fault detection by looking for energy at BPFO/BPFI (+ harmonics) in the envelope spectrum

References: vibration analysis is the standard PdM method for rotating machinery;
envelope analysis of the resonance band is the established way to catch incipient
bearing faults (BPFO/BPFI characteristic frequencies).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np


def time_features(x: np.ndarray) -> Dict[str, float]:
    x = np.asarray(x, dtype=float)
    mu = float(x.mean())
    sigma = float(x.std())
    rms = float(np.sqrt(np.mean(x ** 2)))
    peak = float(np.max(np.abs(x)))
    p2p = float(np.max(x) - np.min(x))
    crest = float(peak / rms) if rms > 0 else 0.0
    kurt = float(np.mean((x - mu) ** 4) / (sigma ** 4) - 3.0) if sigma > 0 else 0.0
    skew = float(np.mean((x - mu) ** 3) / (sigma ** 3)) if sigma > 0 else 0.0
    return {
        "rms": round(rms, 4),
        "peak": round(peak, 4),
        "peak_to_peak": round(p2p, 4),
        "crest_factor": round(crest, 3),
        "kurtosis": round(kurt, 3),
        "skewness": round(skew, 3),
        "std": round(sigma, 4),
    }


def bearing_frequencies(fr: float, n_balls: int = 8, d: float = 8.0,
                        D: float = 40.0, theta_deg: float = 0.0) -> Dict[str, float]:
    """Characteristic defect frequencies from shaft speed fr (Hz) + bearing geometry."""
    ratio = (d / D) * math.cos(math.radians(theta_deg))
    bpfo = (n_balls / 2.0) * fr * (1.0 - ratio)
    bpfi = (n_balls / 2.0) * fr * (1.0 + ratio)
    bsf = (D / (2.0 * d)) * fr * (1.0 - ratio ** 2)
    ftf = 0.5 * fr * (1.0 - ratio)
    return {"shaft": fr, "BPFO": bpfo, "BPFI": bpfi, "BSF": bsf, "FTF": ftf}


def _amplitude_spectrum(x: np.ndarray, fs: float):
    x = np.asarray(x, dtype=float)
    n = len(x)
    win = np.hanning(n)
    xw = (x - x.mean()) * win
    mag = np.abs(np.fft.rfft(xw)) * (2.0 / np.sum(win))
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    return freqs, mag


def _envelope(x: np.ndarray) -> np.ndarray:
    """Amplitude envelope via the analytic signal (FFT-based Hilbert) — pure numpy."""
    x = np.asarray(x, dtype=float) - float(np.mean(x))
    n = len(x)
    X = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    analytic = np.fft.ifft(X * h)
    return np.abs(analytic)


def _envelope_spectrum(x: np.ndarray, fs: float):
    env = _envelope(x)
    env = env - float(np.mean(env))
    n = len(env)
    win = np.hanning(n)
    mag = np.abs(np.fft.rfft(env * win)) * (2.0 / np.sum(win))
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    return freqs, mag


def _downsample(freqs: np.ndarray, mag: np.ndarray, n_out: int = 240) -> List[Dict[str, float]]:
    """Peak-preserving downsample for charting (keeps the max in each bin so peaks survive)."""
    n = len(freqs)
    if n <= n_out:
        return [{"f": round(float(f), 1), "m": round(float(m), 4)} for f, m in zip(freqs, mag)]
    edges = np.linspace(0, n, n_out + 1).astype(int)
    out: List[Dict[str, float]] = []
    for i in range(n_out):
        a, b = edges[i], edges[i + 1]
        if b <= a:
            continue
        j = a + int(np.argmax(mag[a:b]))
        out.append({"f": round(float(freqs[j]), 1), "m": round(float(mag[j]), 4)})
    return out


def _detect_fault(env_freqs: np.ndarray, env_mag: np.ndarray,
                  bf: Dict[str, float], tol: float = 3.0) -> Dict[str, Any]:
    baseline = float(np.median(env_mag)) + 1e-9

    def peak_at(f: float) -> float:
        band = (env_freqs >= f - tol) & (env_freqs <= f + tol)
        return float(np.max(env_mag[band])) if band.any() else 0.0

    ratios: Dict[str, float] = {}
    for name in ("BPFO", "BPFI"):
        f = bf[name]
        amp = peak_at(f) + 0.6 * peak_at(2 * f)  # fundamental + 1st harmonic
        ratios[name] = amp / baseline

    fault = max(ratios, key=lambda k: ratios[k])
    ratio = ratios[fault]
    detected = ratio > 6.0
    label = {"BPFO": "Outer race fault (BPFO)", "BPFI": "Inner race fault (BPFI)"}[fault]
    return {
        "detected": bool(detected),
        "type": label if detected else "Healthy",
        "fault_frequency_hz": round(bf[fault], 1) if detected else None,
        "confidence": round(min(1.0, ratio / 14.0), 2),
        "ratios": {k: round(v, 2) for k, v in ratios.items()},
    }


def analyze(samples: List[float], fs: float, shaft_hz: float,
            bearing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Full analysis of one raw vibration window."""
    x = np.asarray(samples, dtype=float)
    bf = bearing_frequencies(shaft_hz, **(bearing or {}))

    tf = time_features(x)

    freqs, mag = _amplitude_spectrum(x, fs)
    fft_fmax = min(fs / 2.0, 3500.0)
    keep = freqs <= fft_fmax
    spectrum = _downsample(freqs[keep], mag[keep])

    e_freqs, e_mag = _envelope_spectrum(x, fs)
    env_fmax = max(700.0, 6.0 * bf["BPFI"])
    ekeep = e_freqs <= env_fmax
    envelope = _downsample(e_freqs[ekeep], e_mag[ekeep])
    fault = _detect_fault(e_freqs[ekeep], e_mag[ekeep], bf)

    return {
        "time": tf,
        "spectrum": spectrum,
        "envelope": envelope,
        "bearing": {k: round(float(v), 1) for k, v in bf.items()},
        "fault": fault,
    }
