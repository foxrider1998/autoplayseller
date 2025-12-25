# 📚 AutoPlay Seller - Documentation Index

Selamat datang! Ini adalah aplikasi autoplay video untuk livestream jualan yang compatible dengan TikTok Shop, Shopee, dan platform lainnya.

## 🚀 Quick Links

### Getting Started
1. **[README.md](README.md)** - Dokumentasi utama, overview fitur, dan basic usage
2. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Panduan setup lengkap untuk production (100 produk)
3. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Summary project, architecture, dan roadmap

### Installation
- **Quick Setup**: Double-click `setup.bat` (Windows)
- **Manual**: Lihat [README.md - Installation](README.md#-instalasi)

### Usage
- **Run App**: Double-click `run.bat` atau jalankan `python main.py`
- **Test**: Jalankan `python test_app.py` untuk check semua komponen
- **Generate Config**: `python generate_config.py 100` untuk 100 produk

## 📁 File Structure

```
autoplayseller/
│
├── 📄 Core Application Files
│   ├── main.py                    # Main GUI application
│   ├── comment_detector.py        # Comment detection module
│   ├── obs_controller.py          # OBS WebSocket controller
│   └── config.json               # Configuration file
│
├── 🛠️ Helper Scripts
│   ├── generate_config.py        # Generate config for N products
│   ├── test_app.py              # Test all components
│   ├── setup.bat                # Quick setup script (Windows)
│   └── run.bat                  # Run application (Windows)
│
├── 📚 Documentation
│   ├── README.md                # Main documentation
│   ├── SETUP_GUIDE.md          # Detailed setup guide
│   ├── PROJECT_SUMMARY.md      # Project summary
│   ├── BROWSER_EXTENSION.md    # Browser extension guide
│   └── INDEX.md                # This file
│
├── 📁 Data & Config
│   ├── comments.txt            # Comment input file
│   ├── comments_example.txt    # Example comments
│   └── requirements.txt        # Python dependencies
│
└── 🎥 Media
    └── videos/                 # Video files folder
        └── README.md          # Video guide
```

## 🎯 Workflow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Platform   │────▶│   Comment    │────▶│   Keyword   │
│  (TikTok/   │     │   Detector   │     │   Matcher   │
│   Shopee)   │     └──────────────┘     └─────────────┘
└─────────────┘                                  │
                                                 ▼
                                         ┌─────────────┐
                                         │     OBS     │
                                         │  Controller │
                                         └─────────────┘
                                                 │
                                                 ▼
                                         ┌─────────────┐
                                         │ OBS Studio  │
                                         │  (Stream)   │
                                         └─────────────┘
```

## 📖 How to Use This Documentation

### Untuk Pemula (First Time Setup)
1. Baca **[README.md](README.md)** bagian "Instalasi"
2. Jalankan `setup.bat`
3. Ikuti instruksi di console
4. Baca **[SETUP_GUIDE.md](SETUP_GUIDE.md)** bagian "Quick Start"

### Untuk Production (100 Produk)
1. Baca **[SETUP_GUIDE.md](SETUP_GUIDE.md)** bagian "Setup Lengkap"
2. Siapkan 100 video produk
3. Generate config: `python generate_config.py 100`
4. Setup OBS sesuai guide
5. Test dengan 5-10 produk dulu
6. Scale up ke 100

### Untuk Developer (Extend Features)
1. Baca **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** untuk architecture
2. Baca **[BROWSER_EXTENSION.md](BROWSER_EXTENSION.md)** untuk integrasi platform
3. Lihat source code di `main.py`, `comment_detector.py`, `obs_controller.py`
4. Extend sesuai kebutuhan

## 🔧 Common Tasks

### Task 1: Setup Aplikasi
```powershell
# Method 1: Automated
setup.bat

# Method 2: Manual
pip install -r requirements.txt
python generate_config.py 10
python test_app.py
```

### Task 2: Add Video Produk
1. Copy video MP4 ke folder `videos/`
2. Rename: `product_1.mp4`, `product_2.mp4`, dst
3. Update `config.json` jika perlu custom mapping

### Task 3: Setup OBS
1. Install OBS Studio
2. Tools → WebSocket Server Settings
3. Enable server, port 4455
4. Buat Media Source "VideoPlayer"
5. Atur layout scene

### Task 4: Connect Platform (TikTok/Shopee)
**Option A: File-based (Testing)**
- Add comments ke `comments.txt`

**Option B: Browser Extension**
- Follow guide di **[BROWSER_EXTENSION.md](BROWSER_EXTENSION.md)**

**Option C: OCR Screen Capture**
- Follow guide di **[SETUP_GUIDE.md](SETUP_GUIDE.md)** bagian "OCR"

### Task 5: Go Live
1. Start OBS dan setup streaming
2. Run aplikasi: `python main.py`
3. Connect to OBS
4. Start monitoring
5. Test dengan beberapa comment manual
6. Mulai livestream!

## 🐛 Troubleshooting

| Problem | Solution | Doc Reference |
|---------|----------|---------------|
| Tidak bisa connect OBS | Check WebSocket enabled | [README - Troubleshooting](README.md#-troubleshooting) |
| Video tidak play | Check file path & format | [README - Troubleshooting](README.md#-troubleshooting) |
| Comment tidak terdeteksi | Check format & keyword | [README - Troubleshooting](README.md#-troubleshooting) |
| Dependencies error | Run `pip install -r requirements.txt` | [README - Installation](README.md#-instalasi) |
| Config error | Re-generate: `python generate_config.py` | [SETUP_GUIDE](SETUP_GUIDE.md) |

## 📞 Support

### Self-Help Resources
1. Check **[README.md](README.md)** - Troubleshooting section
2. Run `python test_app.py` - Diagnose issues
3. Check log di aplikasi GUI

### Common Questions

**Q: Apakah bisa untuk 100 produk?**
A: Ya! Gunakan `python generate_config.py 100` untuk generate config.

**Q: Platform apa yang support?**
A: TikTok, Shopee, dan platform lain yang bisa di-capture commentnya via file/API/OCR.

**Q: Apakah perlu coding?**
A: Tidak untuk basic usage. Cukup setup config dan video. Coding diperlukan hanya untuk custom integration.

**Q: Gratis atau bayar?**
A: 100% gratis dan open source!

**Q: Video apa yang support?**
A: MP4 (H.264) recommended. Format lain mungkin work tapi optimal pakai MP4.

## 🎓 Learning Path

### Level 1: Beginner (Testing)
- [ ] Install aplikasi
- [ ] Setup OBS basic
- [ ] Test dengan 1-2 produk
- [ ] Gunakan file-based comment

**Time**: 30 menit
**Docs**: [README.md](README.md)

### Level 2: Intermediate (Production Ready)
- [ ] Setup 10-20 produk
- [ ] Create professional video
- [ ] Setup OBS scene layout
- [ ] Test livestream

**Time**: 2-3 jam
**Docs**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Level 3: Advanced (100 Produk + Integration)
- [ ] Scale to 100 produk
- [ ] Browser extension integration
- [ ] Auto-response system
- [ ] Analytics & logging

**Time**: 1-2 hari
**Docs**: [SETUP_GUIDE.md](SETUP_GUIDE.md), [BROWSER_EXTENSION.md](BROWSER_EXTENSION.md)

### Level 4: Expert (Custom Development)
- [ ] API integration
- [ ] Custom features
- [ ] Multi-platform support
- [ ] AI-powered matching

**Time**: Varies
**Docs**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) + Source code

## 🎉 Success Stories

Ready to start? Pick your path:

- **Fast Start**: Run `setup.bat` dan ikuti instruksi
- **Learn More**: Baca [README.md](README.md)
- **Deep Dive**: Baca [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

**Happy Selling! 🚀**

*Last updated: November 2024*
