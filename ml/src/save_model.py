import joblib
from pathlib import Path
from classifier import load_data, train, LABEL_NAMES
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / 'ml' / 'models' / 'ecg_classifier.pkl'


X, y = load_data()
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training 5-class AAMI model...")
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
