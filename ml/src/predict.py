"""Run inference on a single MIT-BIH record and print beat-by-beat results."""
import sys
import joblib
import numpy as np
import wfdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / 'ml' / 'models' / 'ecg_classifier.pkl'
DATA_DIR = str(PROJECT_ROOT / 'ml' / 'data' / 'mitdb')

AAMI_MAP = {
    'N': 0, 'L': 0, 'R': 0, 'e': 0, 'j': 0,
    'A': 1, 'a': 1, 'J': 1, 'S': 1,
    'V': 2, 'E': 2,
    'F': 3,
    '/': 4, 'f': 4, 'Q': 4, '?': 4,
}
LABEL_NAMES = ['N', 'S', 'V', 'F', 'Q']


def extract_features(beat: np.ndarray) -> list:
    return [
        np.mean(beat),
        np.std(beat),
        np.max(beat),
        np.min(beat),
        np.max(beat) - np.min(beat),
        np.median(beat),
        np.sum(beat ** 2),
    ]


def predict_record(record_id: str) -> None:
    if not MODEL_PATH.exists():
        print(f"Model not found at {MODEL_PATH}. Run: python3 ml/src/save_model.py")
        sys.exit(1)

    model = joblib.load(MODEL_PATH)
    record = wfdb.rdrecord(f'{DATA_DIR}/{record_id}')
    annotation = wfdb.rdann(f'{DATA_DIR}/{record_id}', 'atr')
    signal = record.p_signal[:, 0]

    results = []
    for sample, symbol in zip(annotation.sample, annotation.symbol):
        if symbol not in AAMI_MAP:
            continue
        start, end = sample - 180, sample + 180
        if start < 0 or end > len(signal):
            continue
        beat = signal[start:end]
        features = np.array(extract_features(beat)).reshape(1, -1)
        pred = int(model.predict(features)[0])
        prob = model.predict_proba(features)[0][pred]
        true_label = AAMI_MAP[symbol]
        results.append((sample, symbol, pred, prob, true_label))

    correct = sum(r[2] == r[4] for r in results)
    print(f"\nRecord {record_id} — {len(results)} beats, {correct}/{len(results)} correct "
          f"({correct/len(results):.1%})")
    print(f"\n{'Sample':>8}  {'True':>5}  {'Pred':>5}  {'Confidence':>10}  {'Match':>5}")
    print("-" * 48)
    for sample, symbol, pred, prob, true_label in results[:25]:
        match = "✓" if pred == true_label else "✗"
        print(f"{sample:>8}  {symbol:>5}  {LABEL_NAMES[pred]:>5}  {prob:>9.1%}  {match:>5}")
    if len(results) > 25:
        print(f"  ... ({len(results) - 25} more beats)")


if __name__ == '__main__':
    record_id = sys.argv[1] if len(sys.argv) > 1 else '100'
    predict_record(record_id)
