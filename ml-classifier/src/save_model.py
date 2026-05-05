import wfdb
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

DATA_DIR = '/Users/ahmad/Documents/ecg-platform/data/mitdb'

RECORDS = [
    '100','101','102','103','104','105','106','107','108','109',
    '111','112','113','114','115','116','117','118','119','121',
    '122','123','124','200','201','202','203','205','207','208',
    '209','210','212','213','214','215','217','219','220','221',
    '222','223','228','230','231','232','233','234'
]

NORMAL = ['N']

def extract_features(beat):
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
                start = sample - 180
                end = sample + 180
                if start < 0 or end > len(signal):
                    continue
                beat = signal[start:end]
                label = 0 if symbol in NORMAL else 1
                X.append(extract_features(beat))
                y.append(label)
        except Exception as e:
            print(f"Skipping {rec}: {e}")
    return np.array(X), np.array(y)

X, y = load_data()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the model to disk
joblib.dump(model, 'ml-classifier/models/ecg_classifier.pkl')
print("Model saved to ml-classifier/models/ecg_classifier.pkl")
