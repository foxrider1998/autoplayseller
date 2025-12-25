# Setup Guide - AutoPlay Seller

## Quick Start (5 Menit)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Generate Config
```powershell
python generate_config.py 10
```
(Generate config untuk 10 produk pertama)

### 3. Siapkan Video Test
Buat 1-2 video test:
- Copy video apapun (MP4) ke folder `videos/`
- Rename menjadi `product_1.mp4`, `product_2.mp4`
- Atau buat video simple dengan text

### 4. Setup OBS
1. Buka OBS Studio
2. Tools → WebSocket Server Settings
3. Enable WebSocket server (port 4455)
4. Buat Media Source dengan nama "VideoPlayer"

### 5. Jalankan Aplikasi
```powershell
python main.py
```
atau double-click `run.bat`

### 6. Test
1. Click "Connect to OBS" → harus muncul "Connected ✓"
2. Click "Start Monitoring"
3. Buka `comments.txt`, tambahkan:
   ```
   testuser: keranjang 1
   ```
4. Save file → video akan play otomatis!

---

## Setup Lengkap untuk Production

### A. Persiapan Video (Important!)

#### Membuat Video Produk Profesional

**Tools yang Direkomendasikan:**
- **CapCut** (Free, mudah) - Desktop atau Mobile
- **DaVinci Resolve** (Free, professional)
- **Adobe Premiere Pro** (Paid, advanced)
- **Canva** (Online, template ready)

**Format Video:**
```
- Resolusi: 1920x1080 (Full HD)
- FPS: 30fps
- Duration: 10-15 detik (optimal)
- Format: MP4 (H.264)
- Bitrate: 5-8 Mbps
- Audio: AAC, 128-192 kbps
```

**Struktur Video yang Baik:**
```
Detik 0-2  : Hook / Attention grabber
Detik 2-8  : Produk showcase (zoom, angle berbeda)
Detik 8-10 : Price + CTA (Call to Action)
Detik 10+  : Branding (optional)
```

**Template Video:**
1. Background musik upbeat (low volume)
2. Text overlay:
   - Nama produk (besar, bold)
   - Harga (warna mencolok)
   - Stok / Limited info
   - Cara order
3. Product images/footage:
   - Close-up detail
   - Usage demonstration
   - Size comparison
4. Animated transitions

**Tools Text Overlay:**
- Motion graphics dari CapCut
- Lower thirds templates
- Animated price tags
- "LIMITED STOCK" badge

#### Batch Processing Video

Jika punya banyak produk (50-100), gunakan automation:

**Dengan FFmpeg:**
```powershell
# Resize semua video ke 1920x1080
for %f in (*.mp4) do ffmpeg -i "%f" -vf scale=1920:1080 -c:a copy "output/%f"

# Add watermark
ffmpeg -i input.mp4 -i logo.png -filter_complex "overlay=10:10" output.mp4

# Trim duration ke 15 detik
ffmpeg -i input.mp4 -t 15 -c copy output.mp4
```

**Dengan Python Script:**
```python
# batch_process_videos.py
from moviepy.editor import *

for i in range(1, 101):
    # Load image
    img = ImageClip(f"product_images/product_{i}.jpg").set_duration(10)
    
    # Add text
    txt = TextClip(f"Produk {i}\nRp 99.000", 
                   fontsize=70, color='white', 
                   font='Arial-Bold')
    txt = txt.set_position('center').set_duration(10)
    
    # Composite
    video = CompositeVideoClip([img, txt])
    
    # Add audio
    audio = AudioFileClip("background_music.mp3").subclip(0, 10)
    video = video.set_audio(audio)
    
    # Export
    video.write_videofile(f"videos/product_{i}.mp4", fps=30)
```

### B. OBS Studio Setup Detail

#### 1. Scene Layout Design

**Recommended Layout untuk Jualan:**

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────────────┐               │
│  │                     │  [Webcam]     │
│  │   VIDEO PRODUK      │   (kanan)     │
│  │   (VideoPlayer)     │               │
│  │                     │  [Chat Box]   │
│  └─────────────────────┘   (kanan)     │
│                                         │
│  [Logo Toko]      [Promo Banner]       │
└─────────────────────────────────────────┘
```

**Setup Steps:**

1. **Scene 1: Main Scene** (Tampilan utama)
   - Webcam (kanan, circle mask)
   - VideoPlayer (tengah-kiri, 60% width)
   - Logo toko (kiri bawah)
   - Chat overlay (kanan bawah)
   - Background gradient/pattern

2. **Scene 2: Fullscreen Video** (Saat promo besar)
   - VideoPlayer (fullscreen)
   - Logo overlay

3. **Scene 3: BRB Scene**
   - Static image "Sebentar ya..."
   - Background music

#### 2. Media Source Settings

Buat Media Source dengan settings optimal:

```
Source Name: VideoPlayer
Type: Media Source

Settings:
☑ Local File
☐ Loop
☑ Restart playback when source becomes active
☐ Show nothing when playback ends
☑ Use hardware decoding when available

Advanced:
- Speed: 100%
- Color Range: Full
- Hardware Decoding: Yes (jika support)
```

#### 3. Audio Settings

Setup audio mixing:
- Desktop Audio: -10dB (background)
- Mic/Aux: 0dB (your voice)
- VideoPlayer: -5dB (produk video)

Filter audio produk:
- Compressor (threshold: -18dB)
- Limiter (max: -3dB)

#### 4. Transform & Position

```
VideoPlayer Transform:
- Position: X=100, Y=100
- Size: 800x600 (atau fullscreen)
- Crop: Sesuaikan jika perlu
- Blending: Normal
- Scale Filtering: Lanczos (best quality)
```

#### 5. Hotkeys Setup

Berguna untuk manual control:

```
Show VideoPlayer: Ctrl+Alt+V
Hide VideoPlayer: Ctrl+Alt+H
Switch to Main Scene: Ctrl+1
Switch to Video Scene: Ctrl+2
Mute VideoPlayer: Ctrl+Alt+M
```

### C. Integrasi dengan Platform Livestream

#### TikTok Shop Integration

**Method 1: Manual Monitoring**
1. Buka TikTok Live Creator Studio di browser
2. Monitor komentar manual
3. Ketik ke `comments.txt` atau pake hotkey

**Method 2: Browser Extension (Recommended)**

Buat Chrome Extension sederhana:

```javascript
// content_script.js
// Inject ke TikTok Live page

// Monitor chat messages
setInterval(() => {
  const chatMessages = document.querySelectorAll('.chat-message');
  
  chatMessages.forEach(msg => {
    const username = msg.querySelector('.username')?.textContent;
    const text = msg.querySelector('.text')?.textContent;
    
    if (username && text && !processed.has(msg)) {
      processed.add(msg);
      
      // Send to local server
      fetch('http://localhost:8000/comment', {
        method: 'POST',
        body: JSON.stringify({ username, text })
      });
    }
  });
}, 1000);
```

Setup local server di app:
```python
# Add ke main.py
from flask import Flask, request

app = Flask(__name__)

@app.route('/comment', methods=['POST'])
def receive_comment():
    data = request.json
    # Process comment
    return {'status': 'ok'}

# Run in background thread
threading.Thread(target=lambda: app.run(port=8000)).start()
```

**Method 3: OCR Screen Capture**

Gunakan library OCR untuk baca chat:

```python
# ocr_chat_reader.py
import pytesseract
from PIL import ImageGrab

def capture_chat_area():
    # Capture area chat (define coordinates)
    bbox = (1400, 200, 1900, 800)  # x1, y1, x2, y2
    screenshot = ImageGrab.grab(bbox)
    
    # OCR
    text = pytesseract.image_to_string(screenshot, lang='ind')
    
    # Parse comments
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            username, comment = line.split(':', 1)
            # Process comment
            print(f"{username}: {comment}")

# Run every 2 seconds
while True:
    capture_chat_area()
    time.sleep(2)
```

#### Shopee Integration

Shopee Live API lebih restricted, gunakan method serupa:
- Browser extension untuk capture chat
- Screen capture + OCR
- Manual input via file/hotkey

### D. Advanced Features

#### Auto-Response Bot

Tambahkan fitur auto-reply ke chat:

```python
# bot_response.py
import pyautogui
import time

def send_chat_response(text):
    """
    Simulate keyboard untuk ketik response di chat
    """
    # Click chat input box (coordinates)
    pyautogui.click(1500, 900)
    time.sleep(0.2)
    
    # Type response
    pyautogui.write(text, interval=0.05)
    
    # Press enter
    pyautogui.press('enter')

# Integrate ke main app
def on_video_played(match_result):
    response = match_result['response_text']
    send_chat_response(response)
```

#### Database Logging

Track semua transaksi:

```python
# db_logger.py
import sqlite3
from datetime import datetime

class TransactionLogger:
    def __init__(self):
        self.conn = sqlite3.connect('transactions.db')
        self.create_table()
    
    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                username TEXT,
                product_id INTEGER,
                comment TEXT
            )
        ''')
    
    def log(self, username, product_id, comment):
        self.conn.execute(
            'INSERT INTO transactions VALUES (?, ?, ?, ?, ?)',
            (None, datetime.now(), username, product_id, comment)
        )
        self.conn.commit()
```

#### Analytics Dashboard

Tambahkan tab analytics di GUI:

```python
# Tab Statistics
stats_tab = ttk.Frame(notebook)
notebook.add(stats_tab, text="Analytics")

# Chart: Top products
# Chart: Comments per hour
# Chart: Conversion rate
```

### E. Performance Optimization

#### Untuk 100 Produk

**Video Storage:**
- Total size estimate: 100 videos × 20MB = 2GB
- Use SSD for faster loading
- Pre-load videos to RAM (advanced)

**Config Optimization:**
```json
{
  "video_settings": {
    "auto_hide_after_play": true,
    "transition_duration": 0.3,
    "preload_videos": true,
    "cache_size": 10
  }
}
```

**OBS Settings:**
- Output Resolution: 1920x1080
- FPS: 30 (bukan 60, save bandwidth)
- Encoder: NVENC (GPU) jika ada, atau x264 (CPU)
- Bitrate: 4500-6000 kbps untuk streaming

**System Requirements:**
```
Minimal:
- CPU: Intel i5 gen 8 / Ryzen 5
- RAM: 8GB
- GPU: Integrated (HD 630+)
- Storage: 5GB free space

Recommended:
- CPU: Intel i7 / Ryzen 7
- RAM: 16GB
- GPU: NVIDIA GTX 1650+ atau AMD RX 580+
- Storage: SSD dengan 10GB free space
```

### F. Troubleshooting Lanjutan

#### Video Lag/Stuttering

**Solusi:**
1. Lower video bitrate
2. Enable GPU decoding di OBS
3. Close browser tabs
4. Disable preview di OBS saat live

#### Comment Detection Delay

**Solusi:**
1. Reduce `check_interval` di config (0.5 detik)
2. Use API instead of file monitoring
3. Optimize regex patterns

#### OBS Disconnection

**Solusi:**
1. Add auto-reconnect logic:
```python
def auto_reconnect(self):
    while self.running:
        if not self.is_connected():
            try:
                self.connect()
            except:
                pass
        time.sleep(5)
```

---

## Production Checklist

Sebelum go-live, pastikan:

- [ ] Semua video sudah ready dan tested
- [ ] Config.json sudah lengkap 1-100
- [ ] OBS scene layout sudah optimal
- [ ] Test semua keyword (sample 10 produk)
- [ ] Webcam dan mic sudah tested
- [ ] Internet speed minimal 10 Mbps upload
- [ ] Backup config dan video files
- [ ] Manual control sudah familiar
- [ ] Emergency stop button ready

---

**Happy Selling! 🎉**

Jika ada pertanyaan, cek dokumentasi atau test dulu dengan 5-10 produk sebelum scale ke 100.
