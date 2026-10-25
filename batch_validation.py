"""MIT-BIH full-record validation and error localization."""
import numpy as np
import wfdb
from scipy.signal import butter, find_peaks, sosfiltfilt
from validation import reference_beats


def match_peaks(detected, reference, fs, tolerance_ms=150):
    """One-to-one chronological matching with unmatched peak locations."""
    detected = np.sort(np.asarray(detected, dtype=int))
    reference = np.sort(np.asarray(reference, dtype=int))
    tolerance = tolerance_ms * fs / 1000
    i = j = 0
    fp, fn, errors = [], [], []

    while i < len(detected) and j < len(reference):
        delta = detected[i] - reference[j]
        if abs(delta) <= tolerance:
            errors.append(1000 * delta / fs)
            i += 1
            j += 1
        elif delta < 0:
            fp.append(int(detected[i]))
            i += 1
        else:
            fn.append(int(reference[j]))
            j += 1

    fp.extend(map(int, detected[i:]))
    fn.extend(map(int, reference[j:]))
    return fp, fn, errors


def validate_record(record_id="100", lead_name="MLII", window_seconds=20):
    record = wfdb.rdrecord(record_id, pn_dir="mitdb")
    annotation = wfdb.rdann(record_id, "atr", pn_dir="mitdb")
    fs = float(record.fs)

    if lead_name not in record.sig_name:
        raise ValueError(f"Lead {lead_name} is unavailable")

    signal = record.p_signal[:, record.sig_name.index(lead_name)]
    window_samples = int(window_seconds * fs)
    if window_samples < int(fs):
        raise ValueError("Window must be at least one second")

    sos = butter(3, [5, 18], btype="bandpass", fs=fs, output="sos")
    all_fp, all_fn, all_errors = [], [], []
    tp = 0

    for start in range(0, len(signal), window_samples):
        end = min(start + window_samples, len(signal))
        segment = signal[start:end]

        if len(segment) < max(30, int(fs)):
            all_fn.extend(map(int, reference_beats(annotation, start, end)))
            continue

        filtered = sosfiltfilt(sos, segment)
        peaks, _ = find_peaks(
            np.abs(filtered),
            distance=max(1, int(0.25 * fs)),
            prominence=max(np.std(filtered) * 1.1, 1e-8),
        )
        detected = peaks + start
        reference = reference_beats(annotation, start, end)
        fp, fn, errors = match_peaks(detected, reference, fs)
        all_fp.extend(fp)
        all_fn.extend(fn)
        all_errors.extend(errors)
        tp += len(errors)

    fp_count, fn_count = len(all_fp), len(all_fn)
    return {
        "record": record_id,
        "lead": lead_name,
        "TP": tp,
        "FP": fp_count,
        "FN": fn_count,
        "sensitivity": tp / (tp + fn_count) if tp + fn_count else float("nan"),
        "ppv": tp / (tp + fp_count) if tp + fp_count else float("nan"),
        "mean_absolute_error_ms": (
            float(np.mean(np.abs(all_errors))) if all_errors else float("nan")
        ),
        "fp_times_s": [round(x / fs, 3) for x in all_fp],
        "fn_times_s": [round(x / fs, 3) for x in all_fn],
    }


if __name__ == "__main__":
    print(validate_record())
