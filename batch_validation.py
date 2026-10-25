"""Full-record MIT-BIH R-peak validation. Educational/research use only."""
import numpy as np
import wfdb
from scipy.signal import butter, find_peaks, sosfiltfilt
from validation import reference_beats, evaluate_r_peaks


def validate_record(record_id="100", lead_name="MLII", window_seconds=20):
    """Evaluate one MIT-BIH recording in nonoverlapping windows."""
    record = wfdb.rdrecord(record_id, pn_dir="mitdb")
    annotation = wfdb.rdann(record_id, "atr", pn_dir="mitdb")
    fs = float(record.fs)

    if lead_name not in record.sig_name:
        raise ValueError(f"Lead {lead_name} is unavailable")

    signal = record.p_signal[:, record.sig_name.index(lead_name)]
    window_samples = int(window_seconds * fs)
    if window_samples < 10:
        raise ValueError("Window is too short")

    sos = butter(3, [5, 18], btype="bandpass", fs=fs, output="sos")
    totals = {"TP": 0, "FP": 0, "FN": 0}
    errors = []

    for start in range(0, len(signal), window_samples):
        end = min(start + window_samples, len(signal))
        segment = signal[start:end]

        if len(segment) < max(30, int(fs)):
            continue

        filtered = sosfiltfilt(sos, segment)
        peaks, _ = find_peaks(
            np.abs(filtered),
            distance=max(1, int(0.25 * fs)),
            prominence=max(np.std(filtered) * 1.1, 1e-8),
        )

        reference = reference_beats(annotation, start, end)
        result = evaluate_r_peaks(peaks + start, reference, fs, 150)

        for key in totals:
            totals[key] += result[key]
        errors.extend(result["timing_errors_ms"])

    tp, fp, fn = totals["TP"], totals["FP"], totals["FN"]
    totals.update({
        "record": record_id,
        "lead": lead_name,
        "sensitivity": tp / (tp + fn) if tp + fn else float("nan"),
        "ppv": tp / (tp + fp) if tp + fp else float("nan"),
        "mean_absolute_error_ms": (
            float(np.mean(np.abs(errors))) if errors else float("nan")
        ),
    })
    return totals


if __name__ == "__main__":
    print(validate_record())
