from flask import Flask, jsonify, request, render_template
import json
import datetime
import os
import uuid
from flask_cors import CORS

app = Flask(__name__)
# CORS'u etkinleştir: Varsayılan olarak tüm kaynaklardan gelen isteklere izin verir.
# Güvenlik açısından daha katı olmak isterseniz belirli origin'leri belirtebilirsiniz.
CORS(app)

# JSON dosyasının yolu (sunucunun çalıştığı dizinde olmalı)
DATA_FILE = 'data.json'

# Basit bir kullanıcı veritabanı (gerçek uygulamada daha güvenli olmalı)
USERS = {
    "teknofest_user": {
        "sifre": "savasaniha2025",
        "takim_numarasi": 101
    }
}

# Aktif oturumları ve token'ları tutmak için basit bir sözlük
active_tokens = {} # token: username

def load_data():
    """data.json dosyasından verileri yükler."""
    if not os.path.exists(DATA_FILE):
        print(f"Hata: {DATA_FILE} dosyası bulunamadı.")
        return None
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Hata: {DATA_FILE} dosyası geçersiz JSON formatında.")
        return None
    except Exception as e:
        print(f"Veri yüklenirken bir hata oluştu: {e}")
        return None

def authenticate_token(token):
    """Verilen token'ın aktif oturumlarda olup olmadığını kontrol eder."""
    return token in active_tokens

@app.before_request
def check_authorization():
    """
    Belirli API uç noktalarına gelen istekler için kimlik doğrulaması yapar.
    Ana sayfa ('/') ve giriş ('/api/giris') için kimlik doğrulaması gerekli değildir.
    OPTIONS istekleri (CORS ön kontrolü için) de atlanır.
    """
    # Kimlik doğrulama gerektirmeyen yolları belirle
    no_auth_paths = ['/', '/api/giris']

    # Eğer istek, kimlik doğrulama gerektirmeyen bir yola geliyorsa veya OPTIONS isteğiyse atla
    if request.path in no_auth_paths or request.method == 'OPTIONS':
        return

    # Authorization başlığını kontrol et
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Kimlik doğrulama token'ı gerekli veya formatı yanlış (Bearer <token>)."}), 401

    token = auth_header.replace("Bearer ", "")
    if not authenticate_token(token):
        return jsonify({"error": "Geçersiz veya süresi dolmuş token. Lütfen tekrar giriş yapın."}), 401

# --- Web Sitesi Ana Sayfa Uç Noktası ---
@app.route('/', methods=['GET'])
def index():
    """
    Ana sayfaya gelen isteği karşılar ve templates/index.html dosyasını döndürür.
    """
    return render_template('index.html')

# --- API Uç Noktaları ---

@app.route('/api/giris', methods=['POST'])
def giris():
    """Kullanıcı girişi yapar ve geçerli bir token döndürür."""
    data = request.get_json()
    kadi = data.get('kadi')
    sifre = data.get('sifre')

    if kadi in USERS and USERS[kadi]["sifre"] == sifre:
        token = str(uuid.uuid4()) # Benzersiz bir token oluştur
        active_tokens[token] = kadi # Token'ı aktif oturumlara ekle
        takim_numarasi = USERS[kadi]["takim_numarasi"]
        print(f"Kullanıcı '{kadi}' giriş yaptı. Token: {token}")
        return jsonify({"message": "Giriş başarılı.", "token": token, "takim_numarasi": takim_numarasi}), 200
    else:
        return jsonify({"error": "Geçersiz kullanıcı adı veya parola."}), 400

@app.route('/api/telemetri', methods=['GET'])
def get_telemetry():
    """Telemetri verilerini döndürür."""
    data = load_data()
    if data and 'telemetry' in data:
        return jsonify(data['telemetry'])
    return jsonify({"error": "Telemetri verisi bulunamadı veya JSON dosyası okunamadı."}), 500

@app.route('/api/telemetri_gonder', methods=['POST'])
def post_telemetry():
    """Telemetri verilerini alır (kaydetme dokümanla uyumlu değil, sadece alır gibi davranır)."""
    telemetry_data = request.get_json()
    if not telemetry_data:
        return jsonify({"error": "Geçersiz JSON verisi."}), 400

    # Normalde burada gelen telemetri verisi işlenir, kaydedilir veya diğer takımlara gönderilir.
    # Bu örnekte sadece alındığını varsayalım ve dokümandaki gibi bir cevap döndürelim.
    # Gerçek Yarışma sunucusunun davranışı dokümana göre ayarlanmalıdır.

    # Örnek olarak diğer takımların konumlarını ve sunucu saatini döndürelim (dokümandaki gibi)
    response_data = {
        "sunucusaati": get_server_time().json, # Güncel sunucu saatini ekle
        "takim_konum_bilgileri": [
            { "takim_numarasi": 102, "iha_enlem": 40.2300, "iha_boylam": 29.0000, "iha_irtifa": 45 },
            { "takim_numarasi": 103, "iha_enlem": 40.2310, "iha_boylam": 29.0010, "iha_irtifa": 50 }
        ]
    }
    print(f"Telemetri alındı: {telemetry_data.get('takim_numarasi')}")
    return jsonify(response_data), 200


@app.route('/api/sunucusaati', methods=['GET'])
def get_server_time():
    """Sunucu saatini döndürür."""
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
    """HSS koordinat verilerini döndürür."""
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
    return jsonify({"error": "HSS koordinat verisi bulunamadı veya JSON dosyası okunamadı."}), 500

@app.route('/api/kilitlenme_bilgisi', methods=['GET'])
def get_lock_on_info():
    """Kilitlenme bilgisi verilerini döndürür."""
    data = load_data()
    if data and 'lock_on_info' in data:
        return jsonify(data['lock_on_info'])
    return jsonify({"error": "Kilitlenme bilgisi bulunamadı veya JSON dosyası okunamadı."}), 500

@app.route('/api/kamikaze_bilgisi', methods=['GET'])
def get_kamikaze_info():
    """Kamikaze bilgisi verilerini döndürür."""
    data = load_data()
    if data and 'kamikaze_info' in data:
        return jsonify(data['kamikaze_info'])
    return jsonify({"error": "Kamikaze bilgisi bulunamadı veya JSON dosyası okunamadı."}), 500

@app.route('/api/qr_koordinati', methods=['GET'])
def get_qr_coordinates():
    """QR koordinat verilerini döndürür."""
    data = load_data()
    if data and 'qr_coordinates' in data:
        return jsonify(data['qr_coordinates'])
    return jsonify({"error": "QR koordinat bilgisi bulunamadı veya JSON dosyası okunamadı."}), 500

if __name__ == '__main__':
    # data.json dosyasının varlığını kontrol et
    if not os.path.exists(DATA_FILE):
        print(f"Uyarı: '{DATA_FILE}' bulunamadı. Lütfen sunucuyu çalıştırmadan önce oluşturun. Örnek JSON içeriğini kullanabilirsiniz.")
        # İsteğe bağlı: Eğer dosya yoksa, varsayılan bir data.json oluşturabilirsiniz
        # with open(DATA_FILE, 'w', encoding='utf-8') as f:
        #     json.dump({"telemetry": {}, "hss_coordinates": [], "lock_on_info": {}, "kamikaze_info": {}, "qr_coordinates": {}}, f, indent=2)

    # Flask uygulamasını belirtilen IP adresinden ve porttan çalıştır
    # Debug modu açıkken yapılan değişiklikler otomatik algılanır ve sunucu yeniden başlatılır.
    app.run(host='10.88.2.187', port=5000, debug=True)
