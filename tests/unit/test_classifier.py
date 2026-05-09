"""Tests for the ML classifier pipeline."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'ml' / 'src'))
from classifier import extract_features, load_data, AAMI_MAP, LABEL_NAMES, PROJECT_ROOT

MODEL_PATH = PROJECT_ROOT / 'ml' / 'models' / 'ecg_classifier.pkl'


class TestExtractFeatures:
    def test_returns_seven_features(self):
        beat = np.zeros(360)
        assert len(extract_features(beat)) == 7

    def test_flat_signal(self):
        beat = np.ones(360) * 0.5
        features = extract_features(beat)
        assert features[0] == pytest.approx(0.5)   # mean
        assert features[1] == pytest.approx(0.0)   # std
        assert features[2] == pytest.approx(0.5)   # max
        assert features[3] == pytest.approx(0.5)   # min
        assert features[4] == pytest.approx(0.0)   # range
        assert features[5] == pytest.approx(0.5)   # median

    def test_known_signal_energy(self):
        beat = np.array([1.0, 2.0, 3.0])
        features = extract_features(beat)
        assert features[6] == pytest.approx(14.0)  # 1² + 2² + 3²

    def test_zero_signal(self):
        beat = np.zeros(360)
        features = extract_features(beat)
        assert all(f == 0.0 for f in features)

    def test_negative_values(self):
        beat = np.array([-1.0, 0.0, 1.0])
        features = extract_features(beat)
        assert features[3] == pytest.approx(-1.0)  # min
        assert features[4] == pytest.approx(2.0)   # range


class TestAamiMapping:
    def test_five_classes(self):
        assert len(LABEL_NAMES) == 5

    def test_normal_symbols_map_to_zero(self):
        for sym in ['N', 'L', 'R', 'e', 'j']:
            assert AAMI_MAP[sym] == 0, f"Expected {sym} → 0 (N)"

    def test_supraventricular_symbols_map_to_one(self):
        for sym in ['A', 'a', 'J', 'S']:
            assert AAMI_MAP[sym] == 1, f"Expected {sym} → 1 (S)"

    def test_ventricular_symbols_map_to_two(self):
        for sym in ['V', 'E']:
            assert AAMI_MAP[sym] == 2, f"Expected {sym} → 2 (V)"

    def test_fusion_maps_to_three(self):
        assert AAMI_MAP['F'] == 3

    def test_unclassifiable_symbols_map_to_four(self):
        for sym in ['/', 'f', 'Q', '?']:
            assert AAMI_MAP[sym] == 4, f"Expected {sym} → 4 (Q)"

    def test_non_beat_symbols_not_in_map(self):
        non_beat = ['+', '~', '|', '"', 'x', '[', ']', '!', '^']
        for sym in non_beat:
            assert sym not in AAMI_MAP, f"Rhythm annotation '{sym}' should not be classified"


class TestModel:
    @pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not found — run save_model.py first")
    def test_model_predicts_five_classes(self):
        import joblib
        model = joblib.load(MODEL_PATH)
        beat = np.random.randn(360)
        features = np.array(extract_features(beat)).reshape(1, -1)
        pred = model.predict(features)[0]
        assert pred in range(5)

    @pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not found — run save_model.py first")
    def test_model_returns_five_probabilities(self):
        import joblib
        model = joblib.load(MODEL_PATH)
        beat = np.random.randn(360)
        features = np.array(extract_features(beat)).reshape(1, -1)
        proba = model.predict_proba(features)[0]
        assert len(proba) == 5
        assert abs(sum(proba) - 1.0) < 1e-6

    @pytest.mark.skipif(not MODEL_PATH.exists(), reason="Model not found — run save_model.py first")
    def test_model_accuracy_above_threshold(self):
        """Regression guard: overall accuracy should stay above 85%."""
        import joblib
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        model = joblib.load(MODEL_PATH)
        X, y = load_data()
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        acc = accuracy_score(y_test, model.predict(X_test))
        assert acc > 0.85, f"Accuracy dropped to {acc:.4f}"
