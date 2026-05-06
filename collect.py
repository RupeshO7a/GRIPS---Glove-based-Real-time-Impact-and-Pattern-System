import requests
import csv
import time
import os

# 🔥 IMPORTANT: Replace with your laptop's WiFi IP
URL = "http://10.144.162.73:8000/data"   # ← CHANGE THIS

def collect(shot_type, seconds=10):
    os.makedirs('data', exist_ok=True)
    filename = f'data/{shot_type}_{int(time.time())}.csv'

    rows_saved = 0

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)

        # ✅ CSV Header
        writer.writerow([
            'TIME','AX','AY','AZ','GX','GY','GZ',
            'FSR1','FSR2','FSR3','FSR4','LABEL'
        ])

        print(f'\n📡 Recording "{shot_type}" for {seconds} seconds...')
        print('👉 Start movement NOW!\n')

        start = time.time()

        while time.time() - start < seconds:
            try:
                # 🔥 Request data (FAST - no delay)
                res = requests.get(URL, timeout=1)

                if res.status_code != 200:
                    print("⚠️ Server error:", res.status_code)
                    continue

                data = res.json()

                # ✅ Extract sensor values
                ax = data.get('ax', 0)
                ay = data.get('ay', 0)
                az = data.get('az', 0)

                gx = data.get('gx', 0)
                gy = data.get('gy', 0)
                gz = data.get('gz', 0)

                f1 = data.get('f1', 0)
                f2 = data.get('f2', 0)
                f3 = data.get('f3', 0)
                f4 = data.get('f4', 0)

                # ✅ Save row
                row = [
                    time.time(),
                    ax, ay, az,
                    gx, gy, gz,
                    f1, f2, f3, f4,
                    shot_type
                ]

                writer.writerow(row)
                rows_saved += 1

                # ✅ Progress print
                if rows_saved % 50 == 0:
                    print(f'  ✅ {rows_saved} rows saved')

            except Exception as e:
                print("❌ Error:", e)

    print(f'\n✅ DONE. Saved {rows_saved} rows to {filename}')

    # 🚨 Warning if too low
    if rows_saved < 50:
        print('\n⚠️ WARNING: Very few rows collected!')
        print('Check:')
        print('1. ESP32 is sending data (Serial Monitor)')
        print('2. Server IP is correct')
        print('3. Both devices on same WiFi')

# 🚀 RUN
if __name__ == "__main__":
    print('\n🎯 Shot types: straight_drive, pull_shot, cover_drive, idle')
    shot = input('Enter shot type: ').strip()

    if shot == "":
        print("❌ Invalid shot type")
    else:
        collect(shot, seconds=10)