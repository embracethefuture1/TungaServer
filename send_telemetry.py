import requests
import json

# Flask sunucunun URL'si (kendi Render adresini yaz!)
URL = "https://senin-render-url.com/api/telemetri"  # <-- BURAYI GÜNCELLE

# Web panelinden giriş yapıp aldığın JWT tokenı buraya yapıştır
TOKEN = "BURAYA_GIRIS_YAPINCA_ALINAN_TOKEN"  # <-- BURAYI GÜNCELLE

# data.json dosyasından telemetri verisini oku
with open("data.json", "r", encoding="utf-8") as f:
    telemetry_data = json.load(f)["telemetry"]

# Header ve POST isteği
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}
response = requests.post(URL, headers=headers, json=telemetry_data)

print("Status:", response.status_code)
print("Response:", response.text) 