"""
Manual OBS Setup Guide - Video Source Creation
"""

print("""
╔═══════════════════════════════════════════════════════════════╗
║          SETUP OBS UNTUK AUTOPLAY VIDEO                      ║
╚═══════════════════════════════════════════════════════════════╝

Untuk autoplay video berfungsi, ikuti langkah berikut:

┌─────────────────────────────────────────────────────────────┐
│  STEP 1: SIAPKAN VIDEO FILES                                │
└─────────────────────────────────────────────────────────────┘

1. Buat folder 'videos' (sudah ada)
2. Copy video files (.mp4, .mov, .avi) ke folder 'videos/'
   Contoh:
   - videos/product_1.mp4
   - videos/product_2.mp4
   - dll...

┌─────────────────────────────────────────────────────────────┐
│  STEP 2: SETUP OBS SCENE & SOURCE (MANUAL)                  │
└─────────────────────────────────────────────────────────────┘

Buka OBS Studio:

1. **Create Scene** (jika belum ada):
   - Klik kanan di "Scenes" → "Add"
   - Nama: "Main Scene" (atau sesuai config.json)

2. **Add Media Source**:
   - Di "Sources", klik tombol [+] 
   - Pilih "Media Source"
   - Nama: "VideoPlayer" (PENTING: harus sama dengan config!)
   - [OK]

3. **Configure Media Source**:
   ✓ ☐ Local File: (kosongkan dulu atau pilih video sample)
   ✓ ☑ Restart playback when source becomes active
   ✓ ☐ Loop (JANGAN dicentang!)
   ✓ ☑ Close file when inactive
   - [OK]

4. **Posisi & Size Video**:
   - Drag video source untuk posisi
   - Resize sesuai canvas
   - Atau klik kanan → Transform → Fit to screen

┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ENABLE WEBSOCKET (sudah done)                      │
└─────────────────────────────────────────────────────────────┘

✓ Tools → WebSocket Server Settings
✓ Enable WebSocket server: ON
✓ Server Port: 4455
✓ Password: (kosongkan)

┌─────────────────────────────────────────────────────────────┐
│  STEP 4: TEST AUTOPLAY                                      │
└─────────────────────────────────────────────────────────────┘

Setelah setup selesai:

1. Run aplikasi: python main.py
2. Klik "Auto Connect OBS"
3. Tambah comment di comments.txt: "keranjang 1"
4. Video akan otomatis play di OBS!

┌─────────────────────────────────────────────────────────────┐
│  ALTERNATIVE: AUTO-CREATE SOURCE (jika ada video)           │
└─────────────────────────────────────────────────────────────┘

Jika sudah ada video di folder 'videos/', aplikasi akan
OTOMATIS create Media Source "VideoPlayer" saat pertama play!

Cukup:
1. Copy minimal 1 video file ke folder 'videos/'
2. Run aplikasi
3. Test play video

╔═══════════════════════════════════════════════════════════════╗
║  TROUBLESHOOTING                                             ║
╚═══════════════════════════════════════════════════════════════╝

❌ Video tidak play?
   → Check nama source di OBS = "VideoPlayer" (exact match!)
   → Check scene name = "Main Scene" atau sesuai config.json
   → Pastikan video file exists di folder 'videos/'

❌ Source not found error?
   → Manual add Media Source di OBS dulu
   → Atau pastikan ada video file untuk auto-create

❌ Connection failed?
   → OBS WebSocket must be enabled (port 4455)
   → Check firewall tidak block port 4455

""")

# Check current config
import json
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("\n" + "═" * 63)
    print("CURRENT CONFIG:")
    print("═" * 63)
    print(f"Scene Name       : {config['obs_settings']['scene_name']}")
    print(f"Source Name      : {config['obs_settings']['video_source_name']}")
    print(f"OBS Host         : {config['obs_settings']['host']}")
    print(f"OBS Port         : {config['obs_settings']['port']}")
    print("═" * 63)
except:
    pass
