from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import threading
import time
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)

# 🔥 Load AI model
model = joblib.load('model/model.pkl')
le    = joblib.load('model/labels.pkl')

# Global storage
latest  = {}
history = []
buf     = []

# ─────────────────────────────────────────────
# Feature extraction (same as training)
# ─────────────────────────────────────────────
def get_features(df):
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
# RECEIVE DATA FROM ESP32 (FAST + REAL-TIME)
# ─────────────────────────────────────────────
@app.route('/data')
def receive_data():
    global latest, buf

    try:
        row = {
            'TIME': time.time(),
            'AX': float(request.args.get('ax', 0)),
            'AY': float(request.args.get('ay', 0)),
            'AZ': float(request.args.get('az', 0)),
            'GX': float(request.args.get('gx', 0)),
            'GY': float(request.args.get('gy', 0)),
            'GZ': float(request.args.get('gz', 0)),
            'FSR1': float(request.args.get('f1', 4095)),
            'FSR2': float(request.args.get('f2', 4095)),
            'FSR3': float(request.args.get('f3', 4095)),
            'FSR4': float(request.args.get('f4', 4095)),
        }

        # 🔥 Add to buffer (for AI)
        buf.append(row)
        if len(buf) > 50:
            buf.pop(0)

        # 🔥 Instant calculations (NO DELAY)
        grip  = np.mean([row['FSR1'], row['FSR2'],
                         row['FSR3'], row['FSR4']])

        swing = np.sqrt(row['AX']**2 +
                        row['AY']**2 +
                        row['AZ']**2)

        gyro  = np.sqrt(row['GX']**2 +
                        row['GY']**2 +
                        row['GZ']**2)

        # 🔥 Update latest
        latest.update({
            'shot': latest.get('shot', 'idle'),
            'grip': round(grip),
            'swing': round(swing),
            'gyro': round(gyro),
            'fsr1': round(row['FSR1']),
            'fsr2': round(row['FSR2']),
            'fsr3': round(row['FSR3']),
            'fsr4': round(row['FSR4']),
        })

        # 🚀 RETURN DATA INSTANTLY (IMPORTANT FIX)
        return jsonify({
            "ax": row['AX'],
            "ay": row['AY'],
            "az": row['AZ'],
            "gx": row['GX'],
            "gy": row['GY'],
            "gz": row['GZ'],
            "f1": row['FSR1'],
            "f2": row['FSR2'],
            "f3": row['FSR3'],
            "f4": row['FSR4']
        })

    except Exception as e:
        print("❌ Error receiving data:", e)
        return jsonify({"error": "data error"})

# ─────────────────────────────────────────────
# AI PREDICTION THREAD (OPTIMIZED)
# ─────────────────────────────────────────────
def predictor():
    global latest, history, buf

    while True:
        try:
            # 🔥 Use bigger window (more stable + less CPU load)
            if len(buf) >= 20:
                df = pd.DataFrame(buf[-20:])
                ft = get_features(df)

                pred = le.inverse_transform(
                    model.predict(pd.DataFrame([ft]))
                )[0]

                latest['shot'] = pred

                history.append({
                    'shot': pred,
                    'time': time.time()
                })

                if len(history) > 300:
                    history.pop(0)

            # 🔥 Reduce CPU usage
            time.sleep(0.2)

        except Exception as e:
            print("❌ Prediction error:", e)
            time.sleep(0.2)

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route('/')
def dashboard():
    return send_from_directory('app', 'index.html')

@app.route('/live')
def live():
    return jsonify(latest)

@app.route('/history')
def hist():
    return jsonify(history[-100:])

@app.route('/status')
def status():
    return jsonify({
        'connected': bool(latest),
        'buffer_size': len(buf)
    })

# ─────────────────────────────────────────────
# START SERVER
# ─────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=predictor, daemon=True).start()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📡 SMART GLOVE SERVER RUNNING (FAST MODE)")
    print("👉 http://localhost:8000")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app.run(host='0.0.0.0', port=8000, debug=False)