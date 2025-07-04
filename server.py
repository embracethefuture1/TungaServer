from flask import Flask, jsonify, request, render_template
import json
import datetime
import os
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data.json'

USERS = {
    "teknofest_user": {
        "sifre": "savasaniha2025",
        "takim_numarasi": 101
    }
}

active_tokens = {}

def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def authenticate_token(token):
    return token in active_tokens

@app.before_request
def check_authorization():
    no_auth_paths = ['/', '/api/giris']

    if request.path in no_auth_paths or request.method == 'OPTIONS':
        return

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token gerekli veya format hatalı (Bearer <token>)"}), 401

    token = auth_header.replace("Bearer ", "")
    if not authenticate_token(token):
        return jsonify({"error": "Geçersiz veya süresi dolmuş token."}), 401

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/giris', methods=['POST'])
def giris():
    data = request.get_json()
    kadi = data.get('kadi')
    sifre = data.get('sifre')

    if kadi in USERS and USERS[kadi]["sifre"] == sifre:
        token = str(uuid.uuid4())
        active_tokens[token] = kadi
        takim_numarasi = USERS[kadi]["takim_numarasi"]
        return jsonify({"message": "Giriş başarılı.", "token": token, "takim_numarasi": takim_numarasi}), 200
    else:
        return jsonify({"error": "Geçersiz kullanıcı adı veya parola."}), 400

@app.route('/api/telemetri', methods=['GET'])
def get_telemetry():
    data = load_data()
    if data and 'telemetry' in data:
        return jsonify(data['telemetry'])
    return jsonify({"error": "Telemetri verisi bulunamadı."}), 500

@app.route('/api/sunucusaati', methods=['GET'])
def get_server_time():
    now = datetime.datetime.now()
    server_time_data = {
        "gun": now.day,
        "saat": now.hour,
        "dakika": now.minute,
        "saniye": now.second,
        "milisaniye": now.microsecond // 1000
    }
    return jsonify(server_time_data)

@app.route('/api/hss_koordinatlari', methods=['GET'])
def get_hss_coordinates():
    data = load_data()
    if data and 'hss_coordinates' in data:
        now = datetime.datetime.now()
        server_time_data = {
            "gun": now.day,
            "saat": now.hour,
            "dakika": now.minute,
            "saniye": now.second,
            "milisaniye": now.microsecond // 1000
        }
        return jsonify({
            "sunucusaati": server_time_data,
            "hss_koordinat_bilgileri": data['hss_coordinates']
        })
    return jsonify({"error": "HSS koordinat verisi bulunamadı."}), 500

@app.route('/api/kilitlenme_bilgisi', methods=['GET'])
def get_lock_on_info():
    data = load_data()
    if data and 'lock_on_info' in data:
        return jsonify(data['lock_on_info'])
    return jsonify({"error": "Kilitlenme bilgisi bulunamadı."}), 500

@app.route('/api/kamikaze_bilgisi', methods=['GET'])
def get_kamikaze_info():
    data = load_data()
    if data and 'kamikaze_info' in data:
        return jsonify(data['kamikaze_info'])
    return jsonify({"error": "Kamikaze bilgisi bulunamadı."}), 500

@app.route('/api/qr_koordinati', methods=['GET'])
def get_qr_coordinates():
    data = load_data()
    if data and 'qr_coordinates' in data:
        return jsonify(data['qr_coordinates'])
    return jsonify({"error": "QR koordinat bilgisi bulunamadı."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
