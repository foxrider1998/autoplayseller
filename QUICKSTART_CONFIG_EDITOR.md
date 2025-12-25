# 🚀 Quick Start Guide - Config Editor

## Setup dalam 5 Menit dengan Visual Config Editor

### Step 1: Install & Run (1 menit)

```powershell
# Setup dependencies
pip install -r requirements.txt

# Run aplikasi
python main.py
```

### Step 2: Setup OBS (2 menit)

1. Buka OBS Studio
2. **Tools → WebSocket Server Settings**
3. ✅ Enable WebSocket server (port 4455)
4. Buat **Media Source** dengan nama `VideoPlayer`

### Step 3: Add Products via Config Editor (2 menit)

#### Method A: Upload Videos

1. Di aplikasi, klik **File → Edit Config**
2. Klik **"📁 Import Videos"**
3. Pilih semua video produk Anda
4. Videos otomatis di-copy & keywords di-generate!
5. Klik **"💾 Save All"**

#### Method B: Manual Add

1. Klik **"➕ Add New"**
2. Isi form:
   ```
   Keyword: keranjang 1
   Video: [Upload] → pilih product_1.mp4
   Response: Terima kasih! Produk 1 segera diproses 🎉
   ```
3. Klik **"Save"**
4. Repeat untuk produk lainnya
5. Klik **"💾 Save All"**

### Step 4: Test! (30 detik)

1. Klik **"Reload Config"** di main window
2. Klik **"Connect to OBS"**
3. Klik **"Start Monitoring"**
4. Buka `comments.txt`, tambahkan:
   ```
   testuser: keranjang 1
   ```
5. 🎉 Video will auto-play in OBS!

---

## Advanced: Regex Patterns

### Example 1: Multiple Variations
```
Pattern: (keranjang|krnjg|cart)\s*1
✅ Use as Regex Pattern
```
Matches: "keranjang 1", "krnjg 1", "cart 1", "keranjang1"

### Example 2: Range
```
Pattern: keranjang\s*[1-9]
✅ Use as Regex Pattern
```
Matches: "keranjang 1" to "keranjang 9"

### Example 3: Fallback for Typos
```
Pattern: k[ae]r[ae]nj[ae]ng\s*\d+
✅ Use as Regex Pattern
```
Matches: "karanjang", "kerahjang", dll (typo variations)

---

## Video Upload Tips

### Recommended Video Format
- **Format**: MP4 (H.264)
- **Resolution**: 1920x1080 or 1280x720
- **Duration**: 10-20 seconds
- **Bitrate**: 5-8 Mbps
- **FPS**: 30fps

### Naming Convention
```
✅ Good:
- product_1.mp4
- product_2.mp4
- promo_flashsale.mp4

❌ Avoid:
- video (1).mp4
- IMG_20240101.mp4
- untitled.mp4
```

### Batch Import
1. Prepare videos dengan naming yang konsisten
2. Klik **"📁 Import Videos"**
3. Select all → Open
4. Auto-generated keywords based on filename numbers!

---

## Troubleshooting

### ❌ Config Editor tidak muncul
**Fix**: Check aplikasi di taskbar, click untuk bring to front

### ❌ Video tidak play setelah upload
**Fix**: 
1. Check video ada di folder `videos/`
2. Click **"Reload Config"** di main window
3. Test dengan **"Test Video"** button

### ❌ Regex tidak match
**Fix**:
1. Test pattern di https://regex101.com/ (set flavor: Python)
2. Check case sensitivity (default: case insensitive)
3. Use `.*` untuk match any text before/after

### ❌ Cannot save config
**Fix**:
1. Check file permissions on `config.json`
2. Close other apps yang mungkin lock file
3. Backup exists di `config.json.backup`

---

## Keyboard Shortcuts

### In Config Editor
- **Double-click**: Edit keyword
- **Delete key**: Delete selected
- **Ctrl+S**: Save config (if implemented)
- **Esc**: Close dialog

### In Main App
- **F5**: Reload config (if implemented)
- **Ctrl+Q**: Quit app (if implemented)

---

## Next Steps

1. ✅ Add 5-10 products untuk test
2. ✅ Test di OBS dengan sample comments
3. ✅ Setup livestream platform integration
4. ✅ Go live! 🚀

📖 **Full Documentation**: [README.md](README.md)
🎨 **Config Editor Guide**: [UPDATE_CONFIG_EDITOR.md](UPDATE_CONFIG_EDITOR.md)
🛠️ **Advanced Setup**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
