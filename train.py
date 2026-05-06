import pandas as pd
import numpy as np
import glob
import joblib
import os

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

# ─────────────────────────────────────────────
# Feature Extraction
# ─────────────────────────────────────────────
def extract_features(df):
    f = {}

    for col in ['AX','AY','AZ','GX','GY','GZ']:
        f[col+'_mean'] = df[col].mean()
        f[col+'_std']  = df[col].std()
        f[col+'_max']  = df[col].abs().max()

    for fsr in ['FSR1','FSR2','FSR3','FSR4']:
        f[fsr+'_mean'] = df[fsr].mean()
        f[fsr+'_var']  = df[fsr].var()

    mag = np.sqrt(df['AX']**2 + df['AY']**2 + df['AZ']**2)
    f['swing_peak'] = mag.max()
    f['swing_mean'] = mag.mean()

    total = df[['FSR1','FSR2','FSR3','FSR4']].mean().sum()
    f['total_grip']   = total
    f['grip_balance'] = df['FSR1'].mean() / (total + 1)

    return f


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
files = glob.glob('data/*.csv')
print(f"\n📂 Found {len(files)} data files")

X_list, y_list = [], []

WINDOW = 50
STEP = 25

for path in files:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if len(df) < WINDOW:
        print(f"⚠️ Skipping {path} (not enough rows)")
        continue

    label = df['LABEL'].iloc[0]

    for i in range(0, len(df) - WINDOW, STEP):
        window = df.iloc[i:i+WINDOW]
        X_list.append(extract_features(window))
        y_list.append(label)

print(f"\n📊 Total samples created: {len(X_list)}")

if len(X_list) == 0:
    print("❌ No data available for training!")
    exit()


# ─────────────────────────────────────────────
# PREPARE DATA
# ─────────────────────────────────────────────
X = pd.DataFrame(X_list).fillna(0)

le = LabelEncoder()
y = le.fit_transform(y_list)

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ─────────────────────────────────────────────
# TRAIN MODEL
# ─────────────────────────────────────────────
print("\n🤖 Training Random Forest Model...")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)

model.fit(X_tr, y_tr)


# ─────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────
y_pred = model.predict(X_te)

# 🎯 OVERALL ACCURACY
accuracy = accuracy_score(y_te, y_pred) * 100

print("\n" + "="*50)
print("📊 MODEL EVALUATION")
print("="*50)

# 🔥 MAIN OUTPUT (WHAT YOU WANT)
print(f"\n🏆 OVERALL ACCURACY: {accuracy:.2f}%\n")

# (Optional detailed report)
print("📌 Detailed Report:\n")
print(classification_report(y_te, y_pred, target_names=le.classes_))

print("="*50)


# ─────────────────────────────────────────────
# SAVE MODEL
# ─────────────────────────────────────────────
os.makedirs('model', exist_ok=True)

joblib.dump(model, 'model/model.pkl')
joblib.dump(le, 'model/labels.pkl')

print("\n💾 Model saved successfully!")
print("📁 model/model.pkl")

