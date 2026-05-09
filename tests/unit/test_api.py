"""Tests for the Flask REST API (5-class AAMI)."""
import sys
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parents[2] / 'ml' / 'api'))

AAMI_LABELS = ['N', 'S', 'V', 'F', 'Q']


@pytest.fixture
def mock_model():
    """Mock sklearn model that always predicts N (label 0)."""
    m = MagicMock()
    m.predict.return_value = np.array([0])
    m.predict_proba.return_value = np.array([[0.9, 0.05, 0.03, 0.01, 0.01]])
    return m


@pytest.fixture
def client(mock_model):
    import app as api_module
    api_module.model = mock_model
    api_module.app.config['TESTING'] = True
    with api_module.app.test_client() as c:
        yield c


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['model_loaded'] is True


class TestPredict:
    def test_predict_with_signal_returns_aami_label(self, client):
        resp = client.post('/predict', json={'signal': [0.1] * 360})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['prediction'] in AAMI_LABELS
        assert data['label'] in range(5)
        assert 0.0 <= data['confidence'] <= 1.0
        assert 'description' in data

    def test_predict_normal_label(self, client):
        resp = client.post('/predict', json={'signal': [0.0] * 360})
        assert resp.get_json()['prediction'] == 'N'

    def test_predict_with_features(self, client):
        resp = client.post('/predict', json={'features': [0.1, 0.05, 0.3, -0.1, 0.4, 0.1, 0.02]})
        assert resp.status_code == 200
        assert resp.get_json()['prediction'] in AAMI_LABELS

    def test_predict_probabilities_has_five_classes(self, client):
        resp = client.post('/predict', json={'signal': [0.0] * 360})
        proba = resp.get_json()['probabilities']
        assert set(proba.keys()) == set(AAMI_LABELS)

    def test_probabilities_sum_to_one(self, client):
        resp = client.post('/predict', json={'signal': [0.0] * 360})
        proba = resp.get_json()['probabilities']
        assert abs(sum(proba.values()) - 1.0) < 0.01

    def test_predict_wrong_signal_length(self, client):
        assert client.post('/predict', json={'signal': [0.0] * 100}).status_code == 400

    def test_predict_wrong_feature_count(self, client):
        assert client.post('/predict', json={'features': [0.1, 0.2]}).status_code == 400

    def test_predict_missing_body(self, client):
        resp = client.post('/predict', content_type='application/json', data='')
        assert resp.status_code == 400

    def test_predict_no_model(self, client):
        import app as api_module
        original = api_module.model
        api_module.model = None
        assert client.post('/predict', json={'signal': [0.0] * 360}).status_code == 503
        api_module.model = original

    def test_predict_each_aami_class(self, client, mock_model):
        for label in range(5):
            proba = [0.0] * 5
            proba[label] = 1.0
            mock_model.predict.return_value = np.array([label])
            mock_model.predict_proba.return_value = np.array([proba])
            resp = client.post('/predict', json={'signal': [0.0] * 360})
            assert resp.get_json()['prediction'] == AAMI_LABELS[label]


class TestBatchPredict:
    def test_batch_predict(self, client):
        resp = client.post('/predict/batch', json={'beats': [[0.0] * 360, [0.5] * 360]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 2
        assert len(data['results']) == 2

    def test_batch_each_result_has_aami_label(self, client):
        resp = client.post('/predict/batch', json={'beats': [[0.0] * 360]})
        result = resp.get_json()['results'][0]
        assert result['prediction'] in AAMI_LABELS

    def test_batch_wrong_beat_length(self, client):
        assert client.post('/predict/batch', json={'beats': [[0.0] * 100]}).status_code == 400

    def test_batch_missing_body(self, client):
        assert client.post('/predict/batch', json={}).status_code == 400
