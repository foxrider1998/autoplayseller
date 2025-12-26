# AutoPlay Seller - Aplikasi Autoplay Video untuk Livestream Jualan

Aplikasi desktop yang secara otomatis memutar video produk ketika ada komentar "keranjang 1-100" di livestream. Compatible dengan TikTok Shop, Shopee, dan platform jualan online lainnya. Terintegrasi dengan OBS Studio untuk streaming.

## ✨ Fitur Utama

- 🎥 **Autoplay Video**: Otomatis memutar video produk saat ada komentar
- 🔌 **Auto-Detect OBS**: One-click connection, auto-detect OBS & port (NEW!)
- 🎨 **Visual Config Editor**: UI untuk manage keywords & upload video
- 🔤 **Regex Support**: Flexible keyword matching dengan regex pattern
- 🔧 **Konfigurasi Fleksibel**: Mudah mengatur keyword dan video untuk 1-100 produk
- 📺 **Integrasi OBS**: Seamless integration dengan OBS Studio via WebSocket
- 💬 **Multi-Platform**: Support TikTok, Shopee, dan platform lainnya
- 📊 **Real-time Monitoring**: Dashboard untuk monitoring aktivitas dan statistik
- 🎯 **Smart Keyword Matching**: Deteksi otomatis berbagai variasi keyword (keranjang, krnjg, dll)

## 📋 Persyaratan Sistem

- **Windows 10/11** (atau OS lain yang support Python)
- **Python 3.8+** (Download dari https://www.python.org/)
- **OBS Studio** versi 28.0+ (Download dari https://obsproject.com/)
- **obs-websocket plugin** (Built-in di OBS Studio 28+)

## 🚀 Instalasi

### 1. Install Python Dependencies

Buka PowerShell/Command Prompt di folder aplikasi, lalu jalankan:

```powershell
pip install -r requirements.txt
```

Atau install manual:

```powershell
### Sumber Komentar: TikTok Research API

Selain file lokal, Anda dapat menarik komentar langsung dari TikTok Research API `Query Video Comments`.
pip install obs-websocket-py watchdog pillow requests pydantic
```

### 2. Setup OBS Studio
1) Pastikan token akses klien tersedia dari endpoint OAuth `/v2/oauth/token`.

2) Simpan token secara aman via environment variable di Windows PowerShell:

```powershell
$env:TIKTOK_CLIENT_TOKEN = "clt.example12345Example12345Example"
```

3) Ubah konfigurasi `config.json` agar menggunakan sumber `tiktok`:

```json
{
   "comment_source": {
      "type": "tiktok",
      "token_env": "TIKTOK_CLIENT_TOKEN",
      "video_id": 12345678901,
      "fields": "id,text,like_count,reply_count,create_time,video_id,parent_comment_id",
      "max_count": 100,
      "cursor": 0,
      "poll_interval": 2.0
   }
}
```

Catatan:
- Endpoint: `https://open.tiktokapis.com/v2/research/video/comment/list/?fields=...` (HTTP POST)
- Header `Authorization: Bearer <token>` dan `Content-Type: application/json` digunakan otomatis.
- TikTok API tidak mengembalikan username; aplikasi menggunakan placeholder `tiktok:<comment_id>` sebagai `username` untuk keperluan pencocokan.
- Komentar yang berisi informasi pribadi akan dipulihkan sesuai kebijakan API (redaksi otomatis).

Jika kembali ke sumber file, set `comment_source.type` ke `file` seperti sebelumnya.


1. **Install OBS Studio** (jika belum ada)
   - Download: https://obsproject.com/
   - Install dengan default settings

2. **Enable WebSocket Server**
   - Buka OBS Studio
   - Menu: **Tools → WebSocket Server Settings**
   - Centang **"Enable WebSocket server"**
   - Port: `4455` (default)
   - Password: Kosongkan atau isi sesuai kebutuhan
   - Klik **Apply** dan **OK**

3. **Buat Media Source untuk Video**
   - Di OBS, klik **+** di panel **Sources**
   - Pilih **Media Source**
   - Nama: `VideoPlayer` (atau sesuai config)
   - Setting:
     - ✅ Local File
     - ❌ Loop
     - ✅ Restart playback when source becomes active
     - ❌ Show nothing when playback ends
   - Klik **OK**

4. **Atur Layout Scene**
   - Posisikan **VideoPlayer** sesuai kebutuhan
   - Bisa ditaruh di atas webcam atau di area terpisah
   - Resize sesuai ukuran yang diinginkan

## ⚙️ Konfigurasi

### Option 1: Visual Config Editor (Recommended - NEW! 🎉)

1. **Jalankan Aplikasi**
   ```powershell
   python main.py
   ```

2. **Buka Config Editor**
   - Menu → **File → Edit Config**
   - UI visual akan muncul

3. **Tambah Keyword & Video**
   - Klik **"➕ Add New"**
   - Isi keyword (e.g., "keranjang 1")
   - Upload atau browse video
   - Isi response text (optional)
   - Save!

4. **Upload Video**
   - Klik **"Upload"** di dialog editor
   - Pilih video dari komputer
   - Video otomatis di-copy ke folder `videos/`

5. **Gunakan Regex (Advanced)**
   - ✅ Centang "Use as Regex Pattern"
   - Contoh: `(keranjang|krnjg)\s*[1-5]`
   - Match multiple variations sekaligus!

📖 **Detail lengkap**: Lihat [UPDATE_CONFIG_EDITOR.md](UPDATE_CONFIG_EDITOR.md)

### Option 2: Manual Edit `config.json`

```json
{
  "obs_settings": {
    "host": "localhost",
    "port": 4455,
    "password": "",
    "video_source_name": "VideoPlayer",
    "scene_name": "Main Scene"
  },
  "comment_keywords": {
    "keranjang 1": {
      "video_path": "videos/product_1.mp4",
      "response_text": "Terima kasih! Produk 1 akan kami proses"
    },
    "keranjang 2": {
      "video_path": "videos/product_2.mp4",
      "response_text": "Terima kasih! Produk 2 akan kami proses"
    }
    // ... tambahkan hingga 100 produk
  },
  "comment_source": {
    "type": "file",
    "file_path": "comments.txt",
    "check_interval": 1.0
  },
  "video_settings": {
    "auto_hide_after_play": true,
    "transition_duration": 0.5
  }
}
```

### Tambahkan Video Produk

1. Siapkan video produk (format MP4, H.264)
2. Copy ke folder `videos/`
3. Nama sesuai config: `product_1.mp4`, `product_2.mp4`, dll
4. Durasi disarankan: 5-30 detik per video

**Tips Video:**
- Resolusi: 1920x1080 atau 1280x720
- FPS: 30fps
- Bitrate: 5-10 Mbps
- Tambahkan text overlay dengan info produk
- Pastikan audio clear dan tidak terlalu keras

### Generate Config untuk 100 Produk

Gunakan script helper untuk generate config cepat:

```python
# generate_config.py
import json

config = {
    "obs_settings": {
        "host": "localhost",
        "port": 4455,
        "password": "",
        "video_source_name": "VideoPlayer",
        "scene_name": "Main Scene"
    },
    "comment_keywords": {},
    "comment_source": {
        "type": "file",
        "file_path": "comments.txt",
        "check_interval": 1.0
    },
    "video_settings": {
        "auto_hide_after_play": True,
        "transition_duration": 0.5
    }
}

# Generate untuk 100 produk
for i in range(1, 101):
    config["comment_keywords"][f"keranjang {i}"] = {
        "video_path": f"videos/product_{i}.mp4",
        "response_text": f"Terima kasih! Produk {i} akan kami proses"
    }

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✓ Config generated for 100 products!")
```

## 🎮 Cara Penggunaan

### Quick Start (Recommended)

1. **Jalankan Aplikasi**
   ```powershell
   python main.py
   ```

2. **Auto-Connect ke OBS** 🔌
   - Pastikan OBS Studio sudah running
   - Klik tombol **"🔌 Auto Connect OBS"**
   - Aplikasi akan otomatis:
     - ✅ Detect OBS process
     - ✅ Scan WebSocket ports
     - ✅ Connect automatically
     - ✅ Verify scenes & sources
   - Status akan berubah menjadi "Connected ✓"

3. **Start Monitoring**
   - Klik tombol **"▶️ Start Monitoring"**
   - Aplikasi akan mulai membaca file `comments.txt`

4. **Test dengan Komentar**
   - Buka file `comments.txt`
   - Tambahkan baris baru:
     ```
     testuser: keranjang 1
     ```
   - Save file
   - Video akan otomatis play di OBS! 🎉

📖 **Detail Auto-Detect**: Lihat [AUTO_DETECT_OBS.md](AUTO_DETECT_OBS.md)

### Mode 1: Testing dengan File Comments

1. **Jalankan Aplikasi**
   ```powershell
   python main.py
   ```

2. **Connect ke OBS**
   - Klik tombol **"🔌 Auto Connect OBS"** (auto-detect)
   - Atau manual connect jika perlu
   - Pastikan status berubah menjadi "Connected ✓"

3. **Start Monitoring**
   - Klik tombol **"▶️ Start Monitoring"**
   - Aplikasi akan mulai membaca file `comments.txt`

4. **Simulasi Komentar**
   - Buka file `comments.txt`
   - Tambahkan baris baru:
     ```
     [2024-11-09 10:30:00] buyer123: keranjang 1
     ```
   - Save file
   - Video akan otomatis play di OBS!

### Mode 2: Integrasi Live dengan Platform

Untuk integrasi dengan TikTok Shop / Shopee / platform lain, ada beberapa cara:

#### Cara A: Browser Extension (Recommended)

1. Install browser extension untuk capture komentar
2. Extension akan write komentar ke `comments.txt`
3. Aplikasi akan auto-detect dan play video

#### Cara B: Screen Capture + OCR

1. Setup area capture untuk kolom komentar
2. Gunakan OCR untuk baca text komentar
3. Write hasil OCR ke `comments.txt`

#### Cara C: API Integration (Advanced)

Beberapa platform menyediakan API untuk livestream comments:
- Ubah `comment_source.type` di config menjadi `"api"`
- Implementasikan connector ke API platform
- Modify `comment_detector.py` untuk support API

### Tips Livestream

1. **Test Dulu Sebelum Live**
   - Test semua video produk
   - Cek transisi smooth
   - Pastikan audio balance

2. **Backup Plan**
   - Siapkan manual control
   - Bisa pause monitoring jika perlu
   - Test video button untuk demo manual

3. **Optimize Performance**
   - Close aplikasi lain yang tidak perlu
   - Set OBS encoding sesuai internet speed
   - Monitor CPU usage

## 🎯 Workflow Livestream

```
┌─────────────────────┐
│  Platform Jualan    │
│  (TikTok/Shopee)    │
└──────────┬──────────┘
           │ Komentar: "keranjang 1"
           ▼
┌─────────────────────┐
│  Comment Detector   │
│  (File/API)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Keyword Matcher    │
│  Match dengan Config│
└──────────┬──────────┘
           │ Match! → product_1.mp4
           ▼
┌─────────────────────┐
│  OBS Controller     │
│  Play Video         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  OBS Studio         │
│  Stream ke Platform │
└─────────────────────┘
```

## 📁 Struktur File

```
autoplayseller/
├── main.py                 # Aplikasi GUI utama
├── comment_detector.py     # Modul deteksi komentar
├── obs_controller.py       # Modul kontrol OBS
├── config.json            # Konfigurasi aplikasi
├── comments.txt           # File simulasi komentar
├── requirements.txt       # Python dependencies
├── README.md             # Dokumentasi ini
└── videos/               # Folder video produk
    ├── product_1.mp4
    ├── product_2.mp4
    └── ...
```

## 🔧 Troubleshooting

### ❌ "Failed to connect to OBS"

**Solusi:**
1. Pastikan OBS Studio sedang berjalan
2. Check WebSocket server enabled (Tools → WebSocket Server Settings)
3. Cek port dan password di `config.json` sesuai dengan OBS
4. Restart OBS Studio

### ❌ "Video file not found"

**Solusi:**
1. Cek path video di `config.json` benar
2. Pastikan file video ada di folder `videos/`
3. Gunakan format MP4 (H.264)

### ❌ "Media source not found"

**Solusi:**
1. Buat Media Source di OBS dengan nama sesuai config
2. Default nama: `VideoPlayer`
3. Atau ubah `video_source_name` di config sesuai nama source di OBS

### ❌ Video tidak muncul di stream

**Solusi:**
1. Cek source `VideoPlayer` visible di OBS
2. Posisikan layer source di atas elemen lain
3. Cek file video tidak corrupt
4. Test manual play di OBS

### ❌ Komentar tidak terdeteksi

**Solusi:**
1. Check format komentar di `comments.txt` sesuai
2. Pastikan keyword di config match (case insensitive)
3. Cek log aplikasi untuk error
4. Restart monitoring

## 🎨 Customization

### Menambah Variasi Keyword

Edit `comment_detector.py` untuk support lebih banyak variasi:

```python
# Contoh: "krnjg 1", "keranjang1", "cart 1", dll
keywords = {
    "keranjang 1": {...},
    "krnjg 1": {...},      # Typo common
    "keranjang1": {...},   # Tanpa spasi
    "cart 1": {...},       # English
}
```

### Custom Response Action

Tambahkan aksi setelah video play:

```python
def on_video_played(video_path, comment):
    # Send response ke chat (via API)
    # Log ke database
    # Trigger notification
    pass
```

### Multi-Scene Support

Buat scene berbeda untuk kategori produk:

```json
{
  "keranjang 1": {
    "video_path": "videos/product_1.mp4",
    "scene_name": "Fashion Scene"
  },
   Ketika `comment_source.type` adalah `tiktok`, aplikasi akan melakukan polling komentar video sesuai konfigurasi dan mencocokkannya dengan `comment_keywords` seperti sumber file.

  "keranjang 50": {
    "video_path": "videos/product_50.mp4",
    "scene_name": "Electronics Scene"
  }
}
```

## 📊 Monitoring & Analytics

Aplikasi menyediakan statistik real-time:
- Total komentar diterima
- Komentar yang matched
- Total video yang diplay
- Runtime session

Untuk analytics lebih detail, bisa tambahkan logging ke database atau file CSV.

## 🔐 Keamanan & Privacy

- Aplikasi berjalan 100% local di komputer Anda
- Tidak ada data dikirim ke server external
- Komentar disimpan temporary di memory
- Video tidak di-upload ke cloud

## 🤝 Support & Kontribusi

Jika ada pertanyaan atau menemukan bug:
1. Check troubleshooting guide di atas
2. Cek log aplikasi untuk error details
3. Test dengan config minimal (1-2 produk)

## 📜 License

Free to use untuk personal dan komersial.

## 🎉 Credits

Dibuat dengan:
- Python 3
- Tkinter (GUI)
- obs-websocket-py (OBS Integration)
- Watchdog (File monitoring)

---

**Selamat Berjualan! 🚀**
