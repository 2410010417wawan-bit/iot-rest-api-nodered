# IoT REST API dengan Node-RED — Monitoring & Kontrol

Praktikum **Pemrograman Internet of Things (SIF1502) — Pertemuan 9: REST API & Antarmuka Web IoT**.

Node-RED dipakai sebagai backend: menerima data sensor dari MQTT, menyimpannya ke SQLite, menyediakan REST API dan WebSocket, lalu dashboard web buatan sendiri (HTML/CSS/JS) menampilkan datanya.

```
Simulator ESP32 --MQTT--> Mosquitto --> Node-RED --+--> SQLite (history)
   (Python)        iot/sensor                       +--> REST API  (GET/POST/PUT)
        ^                                           +--> WebSocket /ws/sensor
        +------ iot/kontrol <-- POST /api/kontrol --+
                                                         |
                                            dashboard.html (Chart.js)
```

## Tugas pengembangan yang dikerjakan

| # | Tugas | Implementasi |
|---|-------|--------------|
| 1 | Endpoint `PUT /api/threshold` + notifikasi | Batas disimpan di flow context. Saat suhu menyeberang di atas batas, notifikasi dikirim **sekali** ke debug Node-RED dan WebSocket, lalu tampil sebagai banner di dashboard (dan Notification browser jika diizinkan). |
| 2 | Grafik real-time Chart.js | Grafik suhu, kelembaban, dan garis batas suhu di `dashboard.html` |
| 3 | Autentikasi API key | Header `X-API-Key` dicek di setiap endpoint (kecuali preflight `OPTIONS`); salah/kosong membalas `401` |
| 4 | WebSocket di Node-RED | `ws://localhost:1880/ws/sensor`; dashboard menerima data tanpa polling (polling hanya cadangan saat WebSocket putus) |
| 5 | History ke database | SQLite (`iot_history.db`), `/api/history` membaca dari database |

## Struktur berkas

```
flows.json          Flow Node-RED (import langsung)
dashboard.html      Dashboard web
simulasi_esp32.py   Simulator ESP32 (publisher + subscriber kontrol)
requirements.txt    Dependensi Python
```

## Prasyarat

- Node.js dan Node-RED (`localhost:1880`)
- Mosquitto (`localhost:1883`) atau broker MQTT lain
- Python 3 + `paho-mqtt` 2.x
- Node Node-RED **`node-red-node-sqlite`**: menu ☰ → *Manage palette* → *Install* → cari `node-red-node-sqlite`

## Cara menjalankan

```bash
# Terminal 1 - broker MQTT
mosquitto -v

# Terminal 2 - Node-RED (API key opsional lewat environment)
API_KEY=iot-kampus-2026 node-red          # Windows PowerShell: $env:API_KEY="iot-kampus-2026"; node-red

# Terminal 3 - simulator
pip install -r requirements.txt
python simulasi_esp32.py
```

1. Di Node-RED: ☰ → **Import** → pilih `flows.json` → **Deploy**.
2. Buka `dashboard.html` di browser (klik dua kali, atau taruh di folder static Node-RED).
3. Isi batas suhu (mis. `30`) lalu **Simpan Batas**.

Jika `API_KEY` tidak di-set, nilai bawaan adalah `iot-kampus-2026`. Nilai di `CONFIG.API_KEY` pada `dashboard.html` harus sama.

File database `iot_history.db` dibuat otomatis di folder tempat Node-RED dijalankan. Ubah path-nya di node konfigurasi SQLite jika perlu.

## Endpoint

Semua endpoint memerlukan header `X-API-Key`.

| Method | URL | Fungsi |
|--------|-----|--------|
| GET | `/api/suhu` | Data sensor terakhir, batas suhu, notifikasi terakhir |
| GET | `/api/history?limit=50` | History dari SQLite (maks 500, urut lama → baru) |
| POST | `/api/kontrol` | Kirim perintah ke ESP32, body `{"device":"lamp","action":"on"}` |
| PUT | `/api/threshold` | Set batas suhu, body `{"max": 30}` |
| GET | `/api/threshold` | Baca batas suhu |
| WS | `/ws/sensor` | Push `sensor`, `alert`, dan `threshold` |

Contoh uji:

```bash
curl -H "X-API-Key: iot-kampus-2026" http://localhost:1880/api/suhu

curl -X PUT http://localhost:1880/api/threshold \
  -H "X-API-Key: iot-kampus-2026" -H "Content-Type: application/json" \
  -d '{"max": 30}'

curl -X POST http://localhost:1880/api/kontrol \
  -H "X-API-Key: iot-kampus-2026" -H "Content-Type: application/json" \
  -d '{"device":"lamp","action":"on"}'

# tanpa key -> 401
curl -i http://localhost:1880/api/suhu
```

## Verifikasi end-to-end

| Komponen | Cara verifikasi |
|----------|-----------------|
| Simulator → MQTT | Terminal simulator menampilkan `-> Publish: {...}` |
| MQTT → Node-RED | Panel debug menampilkan data sensor |
| Node-RED → SQLite | `/api/history` berisi data; file `iot_history.db` ada |
| Node-RED → REST | `curl` ke `/api/suhu` mengembalikan JSON |
| REST/WebSocket → Web | Angka, grafik, dan tabel dashboard berubah tiap 3 detik, pill WebSocket hijau |
| Threshold | Simpan batas 28 → banner merah muncul, debug Node-RED menampilkan notifikasi |
| Web → REST → MQTT | Klik tombol lampu → simulator menampilkan `<- Perintah diterima` |

## Catatan dan batasan

- **Keamanan:** API key di `dashboard.html` terlihat oleh siapa pun yang membuka berkasnya. Ini autentikasi sederhana untuk praktikum, bukan pengamanan produksi. Untuk produksi gunakan HTTPS dan token per pengguna.
- **WebSocket tidak memakai API key** (browser tidak bisa mengirim header kustom pada WebSocket). Data yang lewat sama dengan `/api/suhu`.
- Batas suhu disimpan di memori (flow context), jadi kembali kosong setelah Node-RED restart.
- Tabel SQLite terus bertambah; tambahkan pembersihan berkala bila dijalankan lama.
- `paho-mqtt` 2.x mewajibkan `mqtt.CallbackAPIVersion.VERSION2` (sudah dipakai di simulator).
- Instalasi `node-red-node-sqlite` di Windows kadang memerlukan build tools; jika gagal, pasang ulang lewat *Manage palette* atau jalankan `npm install node-red-node-sqlite` di folder `~/.node-red`.
