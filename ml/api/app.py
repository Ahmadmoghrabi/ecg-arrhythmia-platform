"""Flask REST API for ECG arrhythmia classification (5-class AAMI)."""
import numpy as np
import joblib
from pathlib import Path
from flask import Flask, request, jsonify

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / 'ml' / 'models' / 'ecg_classifier.pkl'

LABEL_NAMES = ['N', 'S', 'V', 'F', 'Q']
AAMI_MAP = {
    'N': 0, 'L': 0, 'R': 0, 'e': 0, 'j': 0,
    'A': 1, 'a': 1, 'J': 1, 'S': 1,
    'V': 2, 'E': 2,
    'F': 3,
    '/': 4, 'f': 4, 'Q': 4, '?': 4,
}
LABEL_DESCRIPTIONS = {
    'N': 'Normal',
    'S': 'Supraventricular ectopic',
    'V': 'Ventricular ectopic',
    'F': 'Fusion',
    'Q': 'Unclassifiable/Paced',
}

app = Flask(__name__)
model = None


def load_model():
    global model
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run: python3 ml/src/save_model.py"
        )
    model = joblib.load(MODEL_PATH)


def extract_features(signal: list) -> np.ndarray:
    beat = np.array(signal, dtype=float)
    return np.array([
        np.mean(beat),
        np.std(beat),
        np.max(beat),
        np.min(beat),
        np.max(beat) - np.min(beat),
        np.median(beat),
        np.sum(beat ** 2),
    ]).reshape(1, -1)


def build_prediction(label: int, proba: list) -> dict:
    name = LABEL_NAMES[label]
    return {
        'prediction': name,
        'description': LABEL_DESCRIPTIONS[name],
        'label': label,
        'confidence': round(proba[label], 4),
        'probabilities': {
            LABEL_NAMES[i]: round(p, 4) for i, p in enumerate(proba)
        },
    }


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model_loaded': model is not None})


@app.route('/predict', methods=['POST'])
def predict():
    """
    Classify an ECG beat (5-class AAMI: N, S, V, F, Q).

    Accepts either:
      - {"signal": [<360 float samples>]}  — raw ECG window
      - {"features": [<7 floats>]}          — pre-extracted features
    """
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    if 'signal' in data:
        signal = data['signal']
        if len(signal) != 360:
            return jsonify({'error': f'signal must be 360 samples, got {len(signal)}'}), 400
        features = extract_features(signal)

    elif 'features' in data:
        raw = data['features']
        if len(raw) != 7:
            return jsonify({'error': f'features must be 7 values, got {len(raw)}'}), 400
        features = np.array(raw, dtype=float).reshape(1, -1)

    else:
        return jsonify({'error': 'Provide "signal" (360 samples) or "features" (7 values)'}), 400

    label = int(model.predict(features)[0])
    proba = model.predict_proba(features)[0].tolist()
    return jsonify(build_prediction(label, proba))


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """Classify multiple beats. Accepts {"beats": [[360 samples], ...]}"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503

    data = request.get_json(silent=True)
    if not data or 'beats' not in data:
        return jsonify({'error': 'JSON body with "beats" array required'}), 400

    beats = data['beats']
    if not isinstance(beats, list) or len(beats) == 0:
        return jsonify({'error': '"beats" must be a non-empty array'}), 400

    results = []
    for i, signal in enumerate(beats):
        if len(signal) != 360:
            return jsonify({'error': f'beat[{i}] must be 360 samples, got {len(signal)}'}), 400
        features = extract_features(signal)
        label = int(model.predict(features)[0])
        proba = model.predict_proba(features)[0].tolist()
        results.append(build_prediction(label, proba))

    return jsonify({'results': results, 'count': len(results)})


@app.route('/classify/record', methods=['POST'])
def classify_record():
    """
    Classify every beat in a WFDB record.
    Accepts {"record_path": "/absolute/path/to/record"} — no file extension.
    Returns all beats + a summary with counts per AAMI class.
    """
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503

    data = request.get_json(silent=True)
    if not data or 'record_path' not in data:
        return jsonify({'error': '"record_path" is required'}), 400

    try:
        import wfdb
        record = wfdb.rdrecord(data['record_path'])
        annotation = wfdb.rdann(data['record_path'], 'atr')
    except Exception as e:
        return jsonify({'error': f'Could not read record: {str(e)}'}), 400

    signal = record.p_signal[:, 0]
    counts = {name: 0 for name in LABEL_NAMES}
    beats = []

    for sample, symbol in zip(annotation.sample, annotation.symbol):
        if symbol not in AAMI_MAP:
            continue
        start, end = sample - 180, sample + 180
        if start < 0 or end > len(signal):
            continue
        beat = signal[start:end]
        features = extract_features(beat.tolist())
        label = int(model.predict(features)[0])
        proba = model.predict_proba(features)[0].tolist()
        name = LABEL_NAMES[label]
        counts[name] += 1
        beats.append({
            'sampleIndex': int(sample),
            'trueSymbol': symbol,
            **build_prediction(label, proba),
        })

    return jsonify({
        'beats': beats,
        'summary': {
            'totalBeats': len(beats),
            'countsByClass': counts,
            'hasArrhythmia': any(counts[k] > 0 for k in ['S', 'V', 'F', 'Q']),
        },
    })


if __name__ == '__main__':
    load_model()
    print(f"Model loaded from {MODEL_PATH}")
    app.run(debug=True, port=5001)
