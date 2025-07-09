from flask import Flask, jsonify, request, render_template
import json
import datetime
import os
import uuid
from flask_cors import CORS

app = Flask(__name__)
# Tüm kaynaklardan gelen isteklere izin ver (geliştirme için). 
# Üretim ortamında daha kısıtlayıcı olabilirsiniz.
CORS(app) 

# --- Sabitler ---
DATA_FILE = 'data.json'
USERS = {
    "teknofest_user": {
        "sifre": "savasaniha2025",
        "takim_numarasi": 101
    }
}

# --- Uygulama İçi Hafıza (State) ---
# Aktif token'ları burada tutacağız. Sunucu yeniden başladığında silinirler.
active_tokens = {}

# --- Yardımcı Fonksiyonlar ---
def load_data():
    """data.json dosyasını güvenli bir şekilde okur."""
    if not os.path.exists(DATA_FILE):
        return {} # Dosya yoksa boş bir dictionary döndür
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # Dosya boşsa veya geçersizse JSONDecodeError'u yakala
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {} # Hata durumunda da boş dictionary döndür

def save_data(data):
    """Verilen dictionary'i data.json dosyasına yazar."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Dosya yazma hatası: {e}")
        return False

def authenticate_token(token):
    """Verilen token'ın aktif olup olmadığını kontrol eder."""
    return token in active_tokens

# --- Middleware (Her İstekten Önce Çalışan Kod) ---
@app.before_request
def check_authorization():
    """Giriş ve ana sayfa dışındaki tüm endpoint'ler için token kontrolü yapar."""
    # OPTIONS istekleri, CORS preflight için gereklidir, dokunmuyoruz.
    if request.method == 'OPTIONS':
        return
    
    # Kimlik doğrulama gerektirmeyen yollar
    no_auth_paths = ['/', '/api/giris', '/favicon.ico']
    if request.path in no_auth_paths:
        return

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token gerekli veya format hatalı (Bearer <token>)"}), 401
    
    token = auth_header.split(" ")[1]
    if not authenticate_token(token):
        return jsonify({"error": "Geçersiz, süresi dolmuş veya hatalı token."}), 401
    
    # İsteğe kullanıcı bilgisini ekle, böylece endpoint'ler kullanabilir
    request.user_id = active_tokens.get(token)


# --- API Endpoint'leri ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/giris', methods=['POST'])
def giris():
    """Kullanıcı girişi yapar ve token oluşturur."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "İstek gövdesi boş."}), 400

    kadi = data.get('kadi')
    sifre = data.get('sifre')
    
    user = USERS.get(kadi)
    if user and user["sifre"] == sifre:
        token = str(uuid.uuid4())
        active_tokens[token] = kadi # Token'ı aktif et
        return jsonify({
            "message": "Giriş başarılı.", 
            "token": token, 
            "takim_numarasi": user["takim_numarasi"]
        }), 200
    else:
        return jsonify({"error": "Geçersiz kullanıcı adı veya parola."}), 401

@app.route('/api/telemetri', methods=['GET'])
def get_telemetry():
    """En son telemetri verisini döndürür."""
    all_data = load_data()
    telemetry_list = all_data.get('telemetry', [])
    
    if telemetry_list:
        # Listenin son elemanını (en güncel olanı) döndür
        return jsonify(telemetry_list[-1]), 200
    
    # Veri yoksa hata yerine "bekleniyor" durumu döndür
    return jsonify({
        "status": "bekleniyor",
        "mesaj": "Henüz telemetri verisi alınmadı."
    }), 200

@app.route('/api/telemetri', methods=['POST'])
def post_telemetry():
    """İHA'dan gelen telemetri verisini kaydeder."""
    new_telemetry_data = request.get_json()
    if not new_telemetry_data:
        return jsonify({"error": "Geçersiz JSON verisi."}), 400

    all_data = load_data()
    telemetry_list = all_data.get('telemetry', [])
    
    telemetry_list.append(new_telemetry_data)
    
    # Listede sadece son 20 kaydı tut
    all_data['telemetry'] = telemetry_list[-20:]
    
    if save_data(all_data):
        return jsonify({"message": "Telemetri verisi alındı."}), 201
    else:
        return jsonify({"error": "Sunucu hatası: Veri kaydedilemedi."}), 500

def get_data_by_key(key, not_found_message):
    """Belirli bir anahtar için veri döndüren genel fonksiyon."""
    all_data = load_data()
    if key in all_data:
        return jsonify(all_data[key]), 200
    return jsonify({"status": "bekleniyor", "mesaj": not_found_message}), 200

@app.route('/api/sunucusaati', methods=['GET'])
def get_server_time():
    now = datetime.datetime.now()
    return jsonify({
        "gun": now.day,
        "saat": now.hour,
        "dakika": now.minute,
        "saniye": now.second,
        "milisaniye": now.microsecond // 1000
    })

@app.route('/api/hss_koordinatlari', methods=['GET'])
def get_hss_coordinates():
    return get_data_by_key('hss_coordinates', "HSS koordinat verisi bekleniyor.")

@app.route('/api/kilitlenme_bilgisi', methods=['GET'])
def get_lock_on_info():
    return get_data_by_key('lock_on_info', "Kilitlenme bilgisi bekleniyor.")

@app.route('/api/kamikaze_bilgisi', methods=['GET'])
def get_kamikaze_info():
    return get_data_by_key('kamikaze_info', "Kamikaze bilgisi bekleniyor.")

@app.route('/api/qr_koordinati', methods=['GET'])
def get_qr_coordinates():
    return get_data_by_key('qr_coordinates', "QR koordinat bilgisi bekleniyor.")

# --- Sunucuyu Başlatma ---
if __name__ == '__main__':
    # '0.0.0.0' host'u, sunucunun ağdaki tüm arayüzlerden erişilebilir olmasını sağlar.
    # Render gibi platformlar için bu gereklidir.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # debug=True geliştirme sırasında faydalıdır.
