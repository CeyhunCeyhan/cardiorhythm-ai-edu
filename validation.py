"""MIT-BIH R-peak detection validation helpers (research use only)."""
import numpy as np

BEAT_SYMBOLS = frozenset({
    "N", "L", "R", "B", "A", "a", "J", "S", "V", "r",
    "F", "e", "j", "n", "E", "/", "f", "Q", "?"
})


def reference_beats(annotation, start_sample=0, end_sample=None):
    """Select beat annotations within the requested sample window."""
    samples = np.asarray(annotation.sample, dtype=int)
    symbols = np.asarray(annotation.symbol)
    mask = np.isin(symbols, list(BEAT_SYMBOLS))
    mask &= samples >= start_sample
    if end_sample is not None:
        mask &= samples < end_sample
    return samples[mask]


def evaluate_r_peaks(detected_samples, reference_samples, fs, tolerance_ms=150):
    """Compare absolute sample indices with one-to-one matching."""
    if fs <= 0 or tolerance_ms < 0:
        raise ValueError("Invalid sampling rate or tolerance")

    detected = np.sort(np.asarray(detected_samples, dtype=int))
    reference = np.sort(np.asarray(reference_samples, dtype=int))
    tolerance = tolerance_ms * fs / 1000.0

    i = j = 0
    errors_ms = []

    while i < len(detected) and j < len(reference):
        delta = detected[i] - reference[j]
        if abs(delta) <= tolerance:
            errors_ms.append(1000.0 * delta / fs)
            i += 1
            j += 1
        elif delta < 0:
            i += 1
        else:
            j += 1

    tp = len(errors_ms)
    fp = len(detected) - tp
    fn = len(reference) - tp

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "sensitivity": tp / (tp + fn) if tp + fn else float("nan"),
        "ppv": tp / (tp + fp) if tp + fp else float("nan"),
        "mean_absolute_error_ms": (
            float(np.mean(np.abs(errors_ms)))
            if errors_ms else float("nan")
        ),
        "timing_errors_ms": errors_ms,
    }
