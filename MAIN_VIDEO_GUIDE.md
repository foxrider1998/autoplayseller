# Main Video + Promo Video System

## 🎬 Konsep

Sistem autoplay video dengan 2 layer:

1. **Main Video (Background)** 
   - Video utama yang loop terus menerus
   - Sebagai background saat livestream
   - Bisa berisi: intro brand, product showcase, promo umum, dll

2. **Promo Video (Triggered)**
   - Video spesifik product yang dipicu oleh comment
   - Play sekali (tidak loop)
   - Setelah selesai → otomatis kembali ke main video

## 📋 Setup Guide

### Step 1: Prepare Videos

```
videos/
├── main_background.mp4      # Video utama (loop)
├── product_1.mp4            # Video promo product 1
├── product_2.mp4            # Video promo product 2
└── ...
```

**Main Video Tips:**
- Duration: 30-60 detik ideal
- Content: Brand intro, general promo, product catalog
- Format: MP4, 1080p recommended
- Looping friendly (smooth transition end→start)

### Step 2: Configure config.json

```json
{
  "obs_settings": {
    ...
    "main_video_source": "MainVideo",
    "main_video_path": "videos/main_background.mp4"
  },
  "video_settings": {
    "auto_hide_after_play": false,
    "transition_duration": 0.5,
    "return_to_main_video": true,
    "main_video_delay": 1.0
  }
}
```

**Config Options:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `main_video_source` | string | "MainVideo" | Nama OBS source untuk main video |
| `main_video_path` | string | "" | Path ke video background utama |
| `return_to_main_video` | bool | true | Auto-return ke main setelah promo |
| `main_video_delay` | float | 1.0 | Delay (detik) sebelum return |
| `auto_hide_after_play` | bool | false | Hide source setelah play (set false!) |

### Step 3: Setup di OBS Studio

Ada 2 cara:

#### Cara 1: Manual Setup (Recommended)

1. **Buat Scene** (jika belum ada)
   - Nama: "Main Scene" (atau sesuai config)

2. **Add Main Video Source:**
   - Sources → [+] → Media Source
   - Name: **"MainVideo"**
   - ✅ Local File: pilih `main_background.mp4`
   - ✅ **Loop**: CENTANG (penting!)
   - ✅ Restart playback when source becomes active
   - ❌ Close file when inactive: JANGAN centang
   - [OK]

3. **Add Promo Video Source:**
   - Sources → [+] → Media Source  
   - Name: **"VideoPlayer"**
   - ❌ Local File: kosongkan dulu
   - ✅ Restart playback when source becomes active
   - ❌ **Loop**: JANGAN centang (penting!)
   - ✅ Close file when inactive
   - ✅ Show nothing when playback ends
   - [OK]

4. **Atur Layer Order:**
   ```
   Sources (dari atas ke bawah):
   ├── VideoPlayer      (promo - di atas)
   └── MainVideo        (background - di bawah)
   ```

5. **Posisi & Size:**
   - Klik kanan → Transform → Fit to screen (kedua source)
   - Atau resize manual sesuai keinginan

#### Cara 2: Auto-Create (Easy)

Cukup run aplikasi dengan video yang valid, sources akan auto-dibuat!

```powershell
python main.py
# Klik "Auto Connect OBS"
# Sources akan auto-created saat pertama kali play video
```

### Step 4: Test System

```powershell
python test_main_promo_video.py
```

**Expected behavior:**
1. ✅ Main video mulai playing dan loop
2. ✅ Promo video play saat triggered
3. ✅ Setelah promo selesai → auto return ke main
4. ✅ Main video lanjut looping

## 🎯 Usage Flow

### Saat Aplikasi Start

```python
# 1. Connect ke OBS
controller.connect()

# 2. Setup main video (auto-start looping)
controller.setup_main_video()
# → Main video langsung play dan loop
```

### Saat Comment Detected

```python
# Comment: "keranjang 1"
# → Trigger play promo video

controller.play_video(
    "videos/product_1.mp4", 
    is_promo=True
)

# Flow:
# 1. Main video tetap jalan di background
# 2. Promo video play di layer atas (menutupi main)
# 3. Promo selesai → auto-return ke main
# 4. Main video visible lagi dan continue looping
```

### Sequence Diagram

```
Time →
────────────────────────────────────────────────────────
Main:   [=============== LOOPING ================]
        [======== visible ========][== visible ==]
                                   ↑
Promo:                       [play once]
                             [=========]
                                   ↑
Comment:                           └─ "keranjang 1"
```

## 🎨 Advanced Configurations

### A. Different Main Videos

Bisa ganti main video on-the-fly:

```python
# Update config
controller.main_video_path = "videos/night_background.mp4"
controller.setup_main_video()
```

### B. No Main Video (Promo Only)

Set `return_to_main_video: false` di config:

```json
{
  "video_settings": {
    "return_to_main_video": false,
    "auto_hide_after_play": true
  }
}
```

Behavior: Promo play → hide setelah selesai (tidak return)

### C. Custom Return Delay

Adjust delay sebelum return to main:

```json
{
  "video_settings": {
    "main_video_delay": 2.0  // 2 detik delay
  }
}
```

Berguna untuk smooth transition atau fade effect.

### D. Multiple Promo Layers

Untuk advanced users, bisa setup multiple promo sources:

```json
{
  "obs_settings": {
    "video_source_name": "PromoPlayer1",
    "promo_source_2": "PromoPlayer2"
  }
}
```

## 🐛 Troubleshooting

### Main video tidak loop

**Penyebab:** Setting "Loop" tidak aktif di OBS source

**Solusi:**
1. Klik kanan MainVideo source → Properties
2. ✅ Centang "Loop"
3. [OK]

### Promo tidak kembali ke main

**Penyebab:** `return_to_main_video: false` atau main video tidak setup

**Solusi:**
```json
{
  "video_settings": {
    "return_to_main_video": true
  }
}
```

Dan pastikan main video configured:
```json
{
  "obs_settings": {
    "main_video_path": "videos/main_background.mp4"
  }
}
```

### Video overlap/tumpuk

**Penyebab:** Layer order salah di OBS

**Solusi:**
- Drag VideoPlayer (promo) ke atas MainVideo di Sources list
- PromoPlayer harus di layer atas agar visible saat play

### Auto-return terlalu cepat/lambat

**Solusi:** Adjust delay di config:
```json
{
  "video_settings": {
    "main_video_delay": 1.5  // Increase untuk lebih lama
  }
}
```

## 💡 Best Practices

### Main Video Content

✅ DO:
- Durasi 30-90 detik
- Loop-friendly (ending smooth ke beginning)
- Consistent branding
- Product catalog/showcase
- Call-to-action umum

❌ DON'T:
- Video terlalu panjang (>2 menit)
- Ending yang awkward saat loop
- Time-specific content (tanggal, jam)

### Promo Video Content

✅ DO:
- Fokus 1 product
- Durasi 10-30 detik
- Clear product demo
- Price & specs visible
- Strong call-to-action

❌ DON'T:
- Multiple products dalam 1 video
- Terlalu panjang (>45 detik)
- Looping promo (set loop=false!)

### Performance Tips

1. **Video Format:**
   - H.264 codec
   - MP4 container
   - 1080p max (720p OK untuk main)
   - 30fps standard

2. **File Size:**
   - Main video: <50MB
   - Promo video: <30MB
   - Total: keep under 500MB untuk smooth playback

3. **OBS Settings:**
   - Use hardware encoding (NVENC/AMD)
   - Output resolution = video resolution
   - FPS: 30fps

## 📊 Example Configurations

### E-Commerce Fashion

```json
{
  "obs_settings": {
    "main_video_path": "videos/brand_showcase.mp4"
  },
  "comment_keywords": {
    "tas 1": {
      "video_path": "videos/bag_demo.mp4"
    },
    "sepatu 2": {
      "video_path": "videos/shoes_demo.mp4"
    }
  }
}
```

### Food Delivery

```json
{
  "obs_settings": {
    "main_video_path": "videos/menu_catalog.mp4"
  },
  "comment_keywords": {
    "paket 1": {
      "video_path": "videos/nasi_goreng.mp4"
    },
    "paket 2": {
      "video_path": "videos/ayam_geprek.mp4"
    }
  }
}
```

### Electronics

```json
{
  "obs_settings": {
    "main_video_path": "videos/store_intro.mp4"
  },
  "comment_keywords": {
    "hp 1": {
      "video_path": "videos/samsung_review.mp4"
    },
    "laptop 1": {
      "video_path": "videos/asus_demo.mp4"
    }
  }
}
```

## 🚀 Integration dengan Main App

Di `main.py`, autoplay akan handle:

```python
# 1. App start → setup main video
controller.setup_main_video()

# 2. Comment detected → play promo
def on_comment_detected(comment):
    video_path = get_video_for_comment(comment)
    controller.play_video(video_path, is_promo=True)
    # Auto-return handled by controller

# 3. App close → cleanup
controller.disconnect()
```

Semua logic auto-return sudah built-in di `OBSController`!

## ✨ Summary

**Flow:**
1. Main video loop sebagai background
2. Comment trigger → promo play (cover main)
3. Promo selesai → auto kembali ke main
4. Main continue looping → siap trigger berikutnya

**Benefits:**
- ✅ Professional livestream appearance
- ✅ Seamless product demonstrations
- ✅ Always have content on screen
- ✅ Automated return to default state
- ✅ Support unlimited promo videos

**Perfect untuk:**
- TikTok Shop Live
- Shopee Live
- Instagram Live Shopping
- YouTube Live Commerce

---

**Sekarang livestream Anda tidak pernah "blank" lagi!** 🎬✨
