import wfdb
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DATA_DIR = '/Users/ahmad/Documents/ecg-platform/data/mitdb'

# All 48 MIT-BIH records
RECORDS = [
    '100','101','102','103','104','105','106','107','108','109',
    '111','112','113','114','115','116','117','118','119','121',
    '122','123','124','200','201','202','203','205','207','208',
    '209','210','212','213','214','215','217','219','220','221',
    '222','223','228','230','231','232','233','234'
]

# N = Normal, everything else = Arrhythmia
NORMAL = ['N']

def extract_features(beat):
    """Turn a raw beat signal into a feature vector"""
    return [
        np.mean(beat),
        np.std(beat),
        np.max(beat),
        np.min(beat),
        np.max(beat) - np.min(beat),
        np.median(beat),
        np.sum(beat ** 2),  # signal energy
    ]

def load_data():
    X, y = [], []
    print("Loading records...")
    for rec in RECORDS:
        try:
            record = wfdb.rdrecord(f'{DATA_DIR}/{rec}')
            annotation = wfdb.rdann(f'{DATA_DIR}/{rec}', 'atr')
            signal = record.p_signal[:, 0]  # use MLII lead
            
            for i, (sample, symbol) in enumerate(zip(annotation.sample, annotation.symbol)):
                # Extract 360 samples around each beat (180 before, 180 after)
                start = sample - 180
                end = sample + 180
                if start < 0 or end > len(signal):
                    continue
                beat = signal[start:end]
                label = 0 if symbol in NORMAL else 1  # 0=Normal, 1=Arrhythmia
                X.append(extract_features(beat))
                y.append(label)
        except Exception as e:
            print(f"Skipping {rec}: {e}")
    return np.array(X), np.array(y)

def train():
    X, y = load_data()
    print(f"\nTotal beats: {len(y)}")
    print(f"Normal beats: {sum(y==0)}")
    print(f"Arrhythmia beats: {sum(y==1)}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("\nTraining Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Arrhythmia']))
    
    return model

if __name__ == '__main__':
    train()
import joblib
