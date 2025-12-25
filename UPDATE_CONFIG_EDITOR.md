# Update Log - Config Editor UI

## ✨ Fitur Baru - Visual Config Editor

### 📋 Yang Ditambahkan

1. **Config Editor Window** (`config_editor.py`)
   - UI visual untuk manage keywords dan video
   - Tidak perlu edit JSON manual lagi
   - Live preview semua konfigurasi

2. **Regex Pattern Support**
   - Support regex untuk keyword matching yang lebih fleksibel
   - Toggle checkbox untuk enable/disable regex per keyword
   - Regex help & examples built-in

3. **Video Upload & Management**
   - Upload video langsung dari UI
   - Browse existing videos
   - Auto-copy video ke folder `videos/`
   - Batch import multiple videos sekaligus

### 🎯 Cara Menggunakan

#### 1. Membuka Config Editor

Di aplikasi utama:
- Menu → **File → Edit Config**
- Atau shortcut keyboard (jika sudah diset)

#### 2. Menambah Keyword Baru

1. Klik tombol **"➕ Add New"**
2. Dialog akan muncul dengan field:
   - **Keyword/Regex Pattern**: Kata kunci atau regex pattern
   - **Use as Regex Pattern**: Centang jika mau pakai regex
   - **Video File**: Path ke file video
   - **Response Text**: Text response otomatis (optional)

**Contoh Keyword Biasa:**
```
Keyword: keranjang 1
Video: videos/product_1.mp4
Response: Terima kasih! Produk 1 akan kami proses 🎉
```

**Contoh Regex Pattern:**
```
✅ Use as Regex Pattern
Pattern: (keranjang|krnjg|cart)\s*[1-5]
Video: videos/product_bundle_1-5.mp4
Response: Terima kasih! Produk 1-5 akan kami proses 🎉
```

#### 3. Upload Video

**Method A: Upload File Baru**
1. Klik **"Upload"** button
2. Pilih video dari komputer
3. Masukkan nama file yang diinginkan
4. Video akan di-copy ke folder `videos/`

**Method B: Browse Existing**
1. Klik **"Browse..."** button
2. Pilih video yang sudah ada di folder `videos/`

**Method C: Batch Import**
1. Klik **"📁 Import Videos"** di toolbar
2. Pilih multiple video files sekaligus
3. Semua akan di-copy ke `videos/`
4. Auto-generate keywords jika nama file ada angka (e.g., product_1.mp4 → keranjang 1)

#### 4. Edit Keyword

1. **Double-click** pada keyword yang mau di-edit
2. Atau pilih keyword → klik **"Edit"**
3. Edit fields yang diperlukan
4. Klik **"Save"**

#### 5. Delete Keyword

1. Pilih keyword yang mau dihapus
2. Klik **"🗑️ Delete"**
3. Konfirmasi deletion

#### 6. Save Configuration

1. Klik **"💾 Save All"** di toolbar
2. Config akan disimpan ke `config.json`
3. Backup otomatis dibuat: `config.json.backup`
4. Klik **"Reload Config"** di main window untuk apply changes

### 🎨 Regex Pattern Examples

Config editor sudah include regex help. Berikut contoh lengkap:

#### Example 1: Multiple Variations
```regex
(keranjang|krnjg|cart)\s*1
```
Match: "keranjang 1", "krnjg 1", "cart 1", "keranjang1"

#### Example 2: Range of Numbers
```regex
keranjang\s*[1-9]
```
Match: "keranjang 1" sampai "keranjang 9"

#### Example 3: Contains Text
```regex
.*checkout.*
```
Match: Any text containing "checkout"

#### Example 4: Multiple Products
```regex
(keranjang|krnjg)\s*(1|3|5|7|9)
```
Match: keranjang 1, 3, 5, 7, 9 only (odd numbers)

#### Example 5: Price Range
```regex
.*(100k|200k|300k).*
```
Match: Comments mentioning specific prices

#### Example 6: Emoji Support
```regex
.*🛒.*keranjang.*
```
Match: Comments with cart emoji + "keranjang"

### 🔧 Technical Details

**File Changes:**
- ✅ `config_editor.py` - New file (Config editor UI)
- ✅ `main.py` - Updated (integrate config editor)
- ✅ `comment_detector.py` - Updated (regex support)

**New Dependencies:**
- None! Uses built-in tkinter components

**Config JSON Structure:**
```json
{
  "comment_keywords": {
    "keranjang 1": {
      "video_path": "videos/product_1.mp4",
      "response_text": "Terima kasih!",
      "is_regex": false
    },
    "(keranjang|krnjg)\\s*2": {
      "video_path": "videos/product_2.mp4",
      "response_text": "Siap!",
      "is_regex": true
    }
  }
}
```

### 📊 UI Features

**Main Window:**
- Treeview dengan columns: ID | Keyword/Regex | Video File | Response
- Sort & filter support
- Multi-select (untuk future batch operations)

**Toolbar Buttons:**
- ➕ Add New - Add keyword baru
- 🗑️ Delete - Hapus keyword
- 📁 Import Videos - Batch import videos
- 💾 Save All - Save configuration

**Editor Dialog:**
- Keyword/regex input dengan validation
- Regex toggle dengan help text
- Video browser & uploader
- Response text editor
- Save/Cancel buttons

### 🎯 Workflow Example

**Setup 10 Produk dengan Regex:**

1. **Open Config Editor**
   - File → Edit Config

2. **Batch Import Videos**
   - Klik "📁 Import Videos"
   - Pilih 10 video files (product_1.mp4 - product_10.mp4)
   - Auto-generated: "keranjang 1" - "keranjang 10"

3. **Add Regex untuk Variasi**
   - Klik "➕ Add New"
   - Pattern: `(keranjang|krnjg|cart)\s*([1-9]|10)`
   - ✅ Use as Regex Pattern
   - Video: videos/default.mp4
   - Response: "Mohon sebutkan nomor yang jelas ya! 😊"

4. **Save Configuration**
   - Klik "💾 Save All"
   - Klik "Reload Config" di main window

5. **Test**
   - Add comment: "buyer: krnjg 1"
   - Video akan play!

### 🐛 Troubleshooting

**Q: Regex tidak match**
A: 
- Check pattern dengan regex tester online (regex101.com)
- Escape special characters jika perlu
- Case insensitive by default

**Q: Video tidak ditemukan setelah upload**
A:
- Check folder `videos/` ada file-nya
- Check path di config correct (relative path: `videos/filename.mp4`)
- Reload config setelah save

**Q: Config tidak tersimpan**
A:
- Check file permissions
- Check `config.json.backup` untuk restore
- Save manual via JSON editor jika perlu

**Q: Dialog tidak muncul**
A:
- Check aplikasi tidak minimize
- Click di taskbar untuk bring to front
- Restart aplikasi jika stuck

### 💡 Tips & Tricks

**Tip 1: Organize Videos**
```
videos/
├── products/
│   ├── product_1.mp4
│   ├── product_2.mp4
├── promos/
│   ├── flash_sale.mp4
├── responses/
│   ├── thank_you.mp4
```
Gunakan subfolder untuk organize, update path di config

**Tip 2: Priority Matching**
- Regex yang lebih specific sebaiknya di-add duluan
- Config editor shows dalam order
- First match wins

**Tip 3: Test Regex**
- Use online regex tester: https://regex101.com/
- Set flavor: Python
- Test dengan sample comments

**Tip 4: Backup Strategy**
- Auto backup: `config.json.backup` created on every save
- Manual backup: Copy `config.json` ke safe location
- Version control: Use git for config files

**Tip 5: Quick Edit**
- Double-click on row untuk edit cepat
- Tab untuk navigate between fields
- Enter untuk save, Escape untuk cancel

### 🚀 Future Enhancements (Planned)

- [ ] Drag & drop untuk reorder keywords
- [ ] Bulk edit multiple keywords
- [ ] Import/export config to Excel
- [ ] Video preview in editor
- [ ] Test regex dengan sample comments
- [ ] Keyword templates library
- [ ] Video duration preview
- [ ] Auto-suggest regex patterns

---

**Update completed!** Sekarang config management jauh lebih mudah dengan UI visual! 🎉
