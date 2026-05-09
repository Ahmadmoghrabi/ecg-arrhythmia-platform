import wfdb
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(PROJECT_ROOT / 'ml' / 'data' / 'mitdb')

RECORDS = [
    '100','101','102','103','104','105','106','107','108','109',
    '111','112','113','114','115','116','117','118','119','121',
    '122','123','124','200','201','202','203','205','207','208',
    '209','210','212','213','214','215','217','219','220','221',
    '222','223','228','230','231','232','233','234'
]

# AAMI EC57 standard 5-class mapping
AAMI_MAP = {
    'N': 0, 'L': 0, 'R': 0, 'e': 0, 'j': 0,   # N - Normal
    'A': 1, 'a': 1, 'J': 1, 'S': 1,             # S - Supraventricular ectopic
    'V': 2, 'E': 2,                              # V - Ventricular ectopic
    'F': 3,                                      # F - Fusion
    '/': 4, 'f': 4, 'Q': 4, '?': 4,             # Q - Unclassifiable/Paced
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


def load_data():
    X, y = [], []
    print("Loading records...")
    for rec in RECORDS:
        try:
            record = wfdb.rdrecord(f'{DATA_DIR}/{rec}')
            annotation = wfdb.rdann(f'{DATA_DIR}/{rec}', 'atr')
            signal = record.p_signal[:, 0]

            for sample, symbol in zip(annotation.sample, annotation.symbol):
                if symbol not in AAMI_MAP:
                    continue
                start, end = sample - 180, sample + 180
                if start < 0 or end > len(signal):
                    continue
                beat = signal[start:end]
                X.append(extract_features(beat))
                y.append(AAMI_MAP[symbol])
        except Exception as e:
            print(f"Skipping {rec}: {e}")
    return np.array(X), np.array(y)


def train():
    X, y = load_data()
    print(f"\nTotal beats: {len(y)}")
    for i, name in enumerate(LABEL_NAMES):
        print(f"  {name}: {sum(y == i)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\nTraining Random Forest (5-class AAMI)...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=LABEL_NAMES))

    return model


if __name__ == '__main__':
    train()
