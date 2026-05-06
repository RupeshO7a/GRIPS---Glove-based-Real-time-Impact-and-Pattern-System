#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// 🔴 CHANGE THESE ↓↓↓
const char* ssid = "911 september";        // your hotspot name
const char* password = "mugiwara";         // your hotspot password
const char* serverURL = "http://10.144.162.73:8000/data"; // your laptop IP

unsigned long lastTime = 0;
const int interval = 50; // send every 50ms

// Simple smoothing for FSR
int smooth(int pin) {
  int total = 0;
  for (int i = 0; i < 3; i++) {
    total += analogRead(pin);
  }
  return total / 3;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(6, 7);
  delay(500);

  mpu.initialize();

  // 📡 CONNECT TO WIFI
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  if (millis() - lastTime >= interval) {
    lastTime = millis();

    // Read MPU6050
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Read FSR sensors (smoothed)
    int f1 = smooth(0);
    int f2 = smooth(1);
    int f3 = smooth(2);
    int f4 = smooth(3);

    // 📡 SEND DATA TO SERVER
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;

      String url = String(serverURL) +
        "?ax=" + ax +
        "&ay=" + ay +
        "&az=" + az +
        "&gx=" + gx +
        "&gy=" + gy +
        "&gz=" + gz +
        "&f1=" + f1 +
        "&f2=" + f2 +
        "&f3=" + f3 +
        "&f4=" + f4;

      http.begin(url);
      int httpResponseCode = http.GET();

      // 🔍 Debug (optional)
      Serial.print("Sent → ");
      Serial.print(url);
      Serial.print(" | Response: ");
      Serial.println(httpResponseCode);

      http.end();
    } else {
      Serial.println("❌ WiFi Disconnected!");
    }
  }
}