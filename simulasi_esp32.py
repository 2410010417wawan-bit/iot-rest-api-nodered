"""Simulator ESP32: publish data sensor ke MQTT dan terima perintah kontrol.

Jalankan:
    pip install -r requirements.txt
    python simulasi_esp32.py

Variabel lingkungan opsional: MQTT_BROKER (default "localhost"), MQTT_PORT (default 1883).
"""
import json
import os
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC_SENSOR = "iot/sensor"
TOPIC_KONTROL = "iot/kontrol"

lampu = "off"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Terhubung ke broker {BROKER}:{PORT} (reason: {reason_code})")
    client.subscribe(TOPIC_KONTROL)


def on_message(client, userdata, msg):
    global lampu
    try:
        perintah = json.loads(msg.payload.decode())
    except ValueError:
        print(f"<- Perintah tidak valid: {msg.payload!r}")
        return
    print(f"<- Perintah diterima: {perintah}")
    if perintah.get("device") == "lamp" and perintah.get("action") in ("on", "off"):
        lampu = perintah["action"]
        print(f"   Lampu sekarang: {lampu.upper()}")


# paho-mqtt 2.x: wajib menyebut CallbackAPIVersion
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32-Simulator")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

print("ESP32 Simulator berjalan... Ctrl+C untuk stop")
try:
    while True:
        data = {
            # rentang 25-35 supaya batas suhu (mis. 30) mudah terlampaui saat uji
            "suhu": round(random.uniform(25, 35), 1),
            "kelembaban": round(random.uniform(55, 80), 1),
            "timestamp": datetime.now().isoformat(),
        }
        client.publish(TOPIC_SENSOR, json.dumps(data))
        print(f"-> Publish: {data}")
        time.sleep(3)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
