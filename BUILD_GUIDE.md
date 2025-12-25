# Build & Distribution Guide

## 🎯 Overview

Panduan lengkap untuk build AutoPlay Seller menjadi executable (.exe) yang standalone, siap distribute ke user tanpa perlu install Python.

## 📦 Build Options

### Option 1: Batch Script (Recommended untuk Windows)

```powershell
build.bat
```

**Pros:**
- ✅ Simple, double-click aja
- ✅ Auto-install dependencies
- ✅ Auto-create ZIP distribution
- ✅ Clear progress messages

### Option 2: Python Script (Cross-platform)

```powershell
python build.py
```

**Pros:**
- ✅ Works on Windows, Mac, Linux
- ✅ More detailed error messages
- ✅ Programmatic control

### Option 3: Manual PyInstaller

```powershell
# Install PyInstaller
pip install pyinstaller

# Build with spec file
pyinstaller --clean AutoPlaySeller.spec

# Or build without spec
pyinstaller --name=AutoPlaySeller --windowed --onedir main.py
```

## 🚀 Quick Build

### Step-by-Step

1. **Install Build Dependencies**
   ```powershell
   pip install pyinstaller pillow
   ```

2. **Run Build Script**
   ```powershell
   # Method 1: Batch file
   build.bat
   
   # Method 2: Python script
   python build.py
   ```

3. **Wait 2-5 Minutes**
   - PyInstaller analyzing dependencies
   - Compiling executable
   - Copying files

4. **Test Executable**
   ```powershell
   dist\AutoPlaySeller\AutoPlaySeller.exe
   ```

5. **Distribute**
   - Share `AutoPlaySeller-Portable.zip`
   - Or share entire `dist\AutoPlaySeller\` folder

## 📁 Build Output

```
dist/
└── AutoPlaySeller/
    ├── AutoPlaySeller.exe        # Main executable
    ├── config.json               # Configuration
    ├── comments.txt              # Sample comments file
    ├── README.md                 # Documentation
    ├── *.md                      # Other docs
    ├── videos/                   # Videos folder
    │   └── README.md
    └── _internal/                # Python runtime & dependencies
        ├── python313.dll
        ├── obswebsocket/
        ├── watchdog/
        └── ... (all dependencies)
```

## 📊 Build Specifications

### PyInstaller Spec File (`AutoPlaySeller.spec`)

```python
# Key configurations:
- name: 'AutoPlaySeller'
- console: False              # No command prompt window
- windowed: True              # GUI application
- onedir: True                # One folder distribution
- icon: 'icon.ico'            # Custom icon (if exists)

# Included files:
- config.json
- comments.txt
- videos/ folder
- All .md documentation

# Hidden imports (auto-detected dependencies):
- obswebsocket
- watchdog
- psutil
- PIL
```

### Build Size

**Approximate sizes:**
- Executable only: ~500KB
- Full package (with Python runtime): ~40-60MB
- ZIP distribution: ~20-30MB (compressed)

**Note:** Size bisa lebih besar jika include banyak video files.

## 🎨 Custom Icon

### Create Icon File

1. **Get/Create Icon Image**
   - Format: PNG atau JPG
   - Size: 256x256 pixels minimum
   - Logo/brand untuk aplikasi

2. **Convert to ICO**
   
   **Online Tools:**
   - https://www.icoconverter.com/
   - https://convertio.co/png-ico/
   - https://favicon.io/

   **Command Line (ImageMagick):**
   ```powershell
   convert logo.png -define icon:auto-resize=256,128,64,32,16 icon.ico
   ```

3. **Place in Project Root**
   ```
   autoplayseller/
   ├── icon.ico          # ← Your icon file
   ├── main.py
   └── ...
   ```

4. **Rebuild**
   ```powershell
   build.bat
   ```

## 🔧 Advanced Build Options

### Build with Console (for debugging)

Edit `AutoPlaySeller.spec`:
```python
exe = EXE(
    ...
    console=True,  # Change to True
    ...
)
```

Or command line:
```powershell
pyinstaller --name=AutoPlaySeller --onedir --console main.py
```

### Build as Single File

Edit `AutoPlaySeller.spec`:
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,    # Add these
    a.zipfiles,    # Add these
    a.datas,       # Add these
    [],
    name='AutoPlaySeller',
    ...
    onefile=True,  # Add this
)
```

**Pros:** Single .exe file
**Cons:** Slower startup, larger file size

### Optimize Size

```powershell
# Build with UPX compression
pyinstaller --upx-dir=C:\path\to\upx AutoPlaySeller.spec

# Exclude unnecessary modules
pyinstaller --exclude-module=matplotlib --exclude-module=numpy ...
```

### Include Additional Files

Edit `AutoPlaySeller.spec`:
```python
datas=[
    ('config.json', '.'),
    ('videos', 'videos'),
    ('assets', 'assets'),      # Add custom folders
    ('data/*.json', 'data'),   # Include data files
],
```

## 📋 Distribution Checklist

### Before Build
- [ ] Test app thoroughly in dev mode
- [ ] Update version number in code
- [ ] Update README.md with latest info
- [ ] Create/update icon.ico
- [ ] Clean up unnecessary files
- [ ] Test config.json is correct

### After Build
- [ ] Test executable on clean Windows install
- [ ] Verify all features working
- [ ] Check OBS auto-detection
- [ ] Test video playback
- [ ] Verify config editor
- [ ] Check file paths correct

### Distribution Package
- [ ] Include README.md
- [ ] Include all documentation
- [ ] Include sample config.json
- [ ] Include videos/README.md guide
- [ ] Create ZIP with clear name
- [ ] Test ZIP extraction and run

## 📦 Distribution Methods

### Method 1: ZIP File (Recommended)

```
AutoPlaySeller-Portable.zip
├── AutoPlaySeller.exe
├── config.json
├── README.md
├── videos/
└── _internal/
```

**Pros:**
- ✅ Easy to share (email, drive, download)
- ✅ Single file distribution
- ✅ User just extract and run
- ✅ No installer needed

**Distribution:**
- Upload to Google Drive / Dropbox
- Share download link
- Or attach to email (if <25MB)

### Method 2: Installer (Advanced)

Use **Inno Setup** or **NSIS**:

```pascal
; Inno Setup Script
[Setup]
AppName=AutoPlay Seller
AppVersion=1.0
DefaultDirName={pf}\AutoPlaySeller
DefaultGroupName=AutoPlay Seller
OutputDir=output
OutputBaseFilename=AutoPlaySeller-Setup

[Files]
Source: "dist\AutoPlaySeller\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\AutoPlay Seller"; Filename: "{app}\AutoPlaySeller.exe"
```

**Pros:**
- ✅ Professional installation
- ✅ Desktop shortcut
- ✅ Start menu entry
- ✅ Uninstaller included

### Method 3: Microsoft Store (Enterprise)

Requirements:
- Microsoft Partner Account
- App certification
- Packaging for MSIX

## 🐛 Troubleshooting Build Issues

### Issue: "Module not found" error

**Solution:**
Add to `AutoPlaySeller.spec`:
```python
hiddenimports=[
    'missing_module_name',
],
```

### Issue: Build slow/hanging

**Solution:**
- Close other applications
- Disable antivirus temporarily
- Use `--clean` flag
- Delete `build/` folder manually

### Issue: Executable doesn't run

**Solution:**
1. Check if antivirus blocking
2. Try building with `--console` to see errors
3. Test on different PC
4. Ensure all files in `_internal/` copied

### Issue: "DLL not found" error

**Solution:**
- Install Visual C++ Redistributable
- Include specific DLLs in binaries:
```python
binaries=[
    ('C:\\path\\to\\missing.dll', '.'),
],
```

### Issue: Large file size

**Solution:**
- Use UPX compression
- Exclude unused modules
- Build with `--onefile` if needed
- Remove debug symbols: `--strip`

## 📊 Performance Comparison

| Build Type | Startup Time | Size | Distribution |
|------------|--------------|------|--------------|
| Python Script | ~1s | ~5MB | Requires Python |
| PyInstaller (onedir) | ~2-3s | ~50MB | Standalone |
| PyInstaller (onefile) | ~5-7s | ~60MB | Single EXE |
| With UPX | ~2-3s | ~30MB | Compressed |

## 🎯 Recommended Build for Distribution

```powershell
# Build command
pyinstaller --clean AutoPlaySeller.spec

# Result
dist/AutoPlaySeller/
├── AutoPlaySeller.exe (500KB)
└── _internal/ (~45MB)

Total: ~50MB
Compressed ZIP: ~25MB
```

**Why this config:**
- ✅ Fast startup (~2-3s)
- ✅ Easy to update (replace files)
- ✅ Can include videos folder
- ✅ Reasonable size
- ✅ All dependencies included

## 📝 User Instructions (Include in README)

### For End Users:

1. **Download & Extract**
   - Download `AutoPlaySeller-Portable.zip`
   - Extract to any folder (e.g., `C:\AutoPlaySeller`)

2. **Install OBS Studio**
   - Download from https://obsproject.com/
   - Enable WebSocket in OBS settings

3. **Run Application**
   - Double-click `AutoPlaySeller.exe`
   - Click "Auto Connect OBS"
   - Start monitoring!

4. **No Python Required!**
   - Everything is included
   - Just install OBS and run

## 🚀 Automated Build (CI/CD)

### GitHub Actions Example

```yaml
name: Build Executable

on: [push]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: python build.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: AutoPlaySeller-Portable
          path: AutoPlaySeller-Portable.zip
```

## 📄 License & Distribution

- ✅ Free to distribute
- ✅ Can modify for internal use
- ✅ No commercial restrictions
- ✅ Attribution appreciated

## 🎉 Ready to Build!

```powershell
# Quick build
build.bat

# Or
python build.py

# Test
dist\AutoPlaySeller\AutoPlaySeller.exe

# Distribute
# Share: AutoPlaySeller-Portable.zip
```

---

**Build once, run anywhere (Windows)!** 🚀
