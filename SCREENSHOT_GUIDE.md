# 📸 Screenshot Guide - Config Editor

Untuk dokumentasi yang lebih baik, berikut screenshot yang sebaiknya di-capture:

## Main App Screenshots

### 1. Main Window
**File**: `screenshots/main_window.png`
**Show**:
- Status panel (OBS connected)
- Control buttons
- Activity log dengan sample comments
- Statistics

### 2. Config Editor - Main View
**File**: `screenshots/config_editor_main.png`
**Show**:
- Toolbar dengan buttons
- Treeview dengan 5-10 sample keywords
- Status bar

### 3. Config Editor - Add/Edit Dialog
**File**: `screenshots/config_editor_dialog.png`
**Show**:
- Keyword input field
- Regex checkbox (unchecked)
- Video file browser
- Response text area
- Save/Cancel buttons

### 4. Config Editor - Regex Mode
**File**: `screenshots/config_editor_regex.png`
**Show**:
- Regex checkbox (checked)
- Regex help text visible
- Sample regex pattern in keyword field

### 5. Video Upload Dialog
**File**: `screenshots/video_upload.png`
**Show**:
- File browser dialog
- Multiple video files selected
- Upload button

## How to Capture

### Windows (Snipping Tool)
```
1. Open app to desired state
2. Press Win + Shift + S
3. Select area to capture
4. Save to screenshots/ folder
```

### Full Window Capture
```
1. Focus on window
2. Press Alt + PrtScn
3. Paste in image editor
4. Save to screenshots/ folder
```

## Recommended Tools

- **Windows Snipping Tool** (Built-in)
- **ShareX** (Free, advanced features)
- **Greenshot** (Free, annotations)
- **Lightshot** (Quick upload)

## Screenshot Specs

- **Format**: PNG (for quality) or JPG (for size)
- **Resolution**: Original or 1920x1080 max
- **Annotations**: Add arrows, boxes for key features
- **File size**: Optimize to < 500KB per image

## Optional: GIF Demos

Create animated GIFs untuk common workflows:

### 1. Add Keyword Workflow
**File**: `screenshots/demo_add_keyword.gif`
**Show**:
1. Click "Add New"
2. Fill form
3. Upload video
4. Save
5. See new entry in list

### 2. Batch Import Workflow
**File**: `screenshots/demo_batch_import.gif`
**Show**:
1. Click "Import Videos"
2. Select multiple files
3. Auto-generation progress
4. Final list with new keywords

### 3. Edit & Test Workflow
**File**: `screenshots/demo_edit_test.gif`
**Show**:
1. Double-click keyword
2. Edit values
3. Save
4. Reload config
5. Test with comment
6. Video plays in OBS

## Tools for GIF Creation

- **ScreenToGif** (Windows, free, easy)
- **LICEcap** (Windows/Mac, simple)
- **Peek** (Linux, GTK)
- **Kap** (Mac, modern UI)

## GIF Settings

- **FPS**: 10-15 fps (smooth but not too large)
- **Resolution**: 1280x720 or smaller
- **Duration**: 10-30 seconds max
- **File size**: < 5MB per GIF
- **Loop**: Yes (infinite)

---

## Where to Put Screenshots

Update documentation files dengan image embeds:

### README.md
```markdown
## Config Editor

![Config Editor](screenshots/config_editor_main.png)

### Adding Keywords

![Add Dialog](screenshots/config_editor_dialog.png)
```

### UPDATE_CONFIG_EDITOR.md
```markdown
## UI Overview

![Main View](screenshots/config_editor_main.png)

## Adding Keywords

![Dialog](screenshots/config_editor_dialog.png)

## Regex Support

![Regex Mode](screenshots/config_editor_regex.png)
```

---

## Priority Screenshots (Must Have)

1. ✅ Config Editor Main View
2. ✅ Add/Edit Dialog
3. ✅ Regex Mode Active
4. ⭐ Main App with Activity Log
5. ⭐ OBS Integration (video playing)

## Optional Screenshots (Nice to Have)

- Batch import in progress
- Error dialogs (validation)
- Success messages
- Context menus (if any)
- Multiple windows side-by-side

---

**Note**: Screenshots akan membuat dokumentasi lebih jelas dan user-friendly!
