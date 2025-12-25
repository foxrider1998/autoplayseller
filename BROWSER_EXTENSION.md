# Browser Extension untuk Capture Komentar TikTok Live

Folder ini berisi contoh browser extension untuk capture komentar dari TikTok Live.

## Cara Install Extension (Chrome/Edge)

### 1. Buat Folder Extension

Buat folder baru: `tiktok-comment-capture/`

### 2. Buat manifest.json

```json
{
  "manifest_version": 3,
  "name": "TikTok Live Comment Capture",
  "version": "1.0",
  "description": "Capture comments from TikTok Live for AutoPlay Seller",
  "permissions": [
    "activeTab",
    "storage"
  ],
  "host_permissions": [
    "https://www.tiktok.com/*",
    "https://live.tiktok.com/*"
  ],
  "content_scripts": [
    {
      "matches": [
        "https://www.tiktok.com/*/live",
        "https://live.tiktok.com/*"
      ],
      "js": ["content.js"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icon16.png",
      "48": "icon48.png",
      "128": "icon128.png"
    }
  }
}
```

### 3. Buat content.js

```javascript
// content.js - Script yang inject ke TikTok Live page

console.log('TikTok Comment Capture loaded');

let processedComments = new Set();
let isCapturing = false;

// Get settings from storage
chrome.storage.sync.get(['captureEnabled', 'serverUrl'], function(result) {
  isCapturing = result.captureEnabled || false;
  serverUrl = result.serverUrl || 'http://localhost:8000';
});

// Listen for settings changes
chrome.storage.onChanged.addListener(function(changes, namespace) {
  if (changes.captureEnabled) {
    isCapturing = changes.captureEnabled.newValue;
  }
  if (changes.serverUrl) {
    serverUrl = changes.serverUrl.newValue;
  }
});

// Main function to monitor comments
function monitorComments() {
  if (!isCapturing) return;
  
  // TikTok Live chat selectors (may need adjustment)
  const chatSelectors = [
    '.chat-message',
    '[data-e2e="live-chat-message"]',
    // Add more selectors as needed
  ];
  
  let messages = [];
  
  // Try each selector
  for (const selector of chatSelectors) {
    const found = document.querySelectorAll(selector);
    if (found.length > 0) {
      messages = Array.from(found);
      break;
    }
  }
  
  messages.forEach(msgElement => {
    // Skip if already processed
    if (processedComments.has(msgElement)) return;
    
    try {
      // Extract username and comment text
      // (selectors may need adjustment based on TikTok's HTML structure)
      const usernameEl = msgElement.querySelector('.username, [data-e2e="comment-username"]');
      const textEl = msgElement.querySelector('.text, [data-e2e="comment-text"]');
      
      if (usernameEl && textEl) {
        const username = usernameEl.textContent.trim();
        const text = textEl.textContent.trim();
        
        // Mark as processed
        processedComments.add(msgElement);
        
        // Send to local server
        sendComment(username, text);
        
        // Also save to local storage as backup
        saveCommentLocal(username, text);
      }
    } catch (error) {
      console.error('Error processing comment:', error);
    }
  });
  
  // Clean up old processed comments (keep last 1000)
  if (processedComments.size > 1000) {
    const arr = Array.from(processedComments);
    processedComments = new Set(arr.slice(-1000));
  }
}

// Send comment to local server (AutoPlay Seller app)
function sendComment(username, text) {
  fetch(`${serverUrl}/comment`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: username,
      text: text,
      timestamp: new Date().toISOString(),
      platform: 'tiktok'
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Comment sent:', username, text);
  })
  .catch(error => {
    console.error('Error sending comment:', error);
    // Fallback: write to file (if web server not available)
  });
}

// Save to local storage as backup
function saveCommentLocal(username, text) {
  chrome.storage.local.get(['comments'], function(result) {
    let comments = result.comments || [];
    comments.push({
      username: username,
      text: text,
      timestamp: new Date().toISOString()
    });
    
    // Keep only last 100 comments
    if (comments.length > 100) {
      comments = comments.slice(-100);
    }
    
    chrome.storage.local.set({ comments: comments });
  });
}

// Run monitoring every second
setInterval(monitorComments, 1000);

// Initial run
setTimeout(monitorComments, 2000);
```

### 4. Buat popup.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      width: 300px;
      padding: 15px;
      font-family: Arial, sans-serif;
    }
    h3 {
      margin-top: 0;
    }
    .status {
      padding: 10px;
      border-radius: 5px;
      margin-bottom: 10px;
    }
    .status.active {
      background-color: #d4edda;
      color: #155724;
    }
    .status.inactive {
      background-color: #f8d7da;
      color: #721c24;
    }
    button {
      width: 100%;
      padding: 10px;
      margin: 5px 0;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-size: 14px;
    }
    .btn-primary {
      background-color: #007bff;
      color: white;
    }
    .btn-success {
      background-color: #28a745;
      color: white;
    }
    .btn-danger {
      background-color: #dc3545;
      color: white;
    }
    input {
      width: 100%;
      padding: 8px;
      margin: 5px 0;
      box-sizing: border-box;
    }
  </style>
</head>
<body>
  <h3>TikTok Comment Capture</h3>
  
  <div id="status" class="status inactive">
    Status: <span id="statusText">Inactive</span>
  </div>
  
  <label>Server URL:</label>
  <input type="text" id="serverUrl" placeholder="http://localhost:8000" />
  
  <button id="toggleBtn" class="btn-primary">Start Capture</button>
  <button id="testBtn" class="btn-success">Test Connection</button>
  <button id="clearBtn" class="btn-danger">Clear Storage</button>
  
  <div style="margin-top: 15px; font-size: 12px; color: #666;">
    <p><strong>Instructions:</strong></p>
    <ol style="padding-left: 20px;">
      <li>Start AutoPlay Seller app</li>
      <li>Open TikTok Live page</li>
      <li>Click "Start Capture"</li>
      <li>Comments will be sent to app</li>
    </ol>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

### 5. Buat popup.js

```javascript
// popup.js - Popup control script

document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('toggleBtn');
  const testBtn = document.getElementById('testBtn');
  const clearBtn = document.getElementById('clearBtn');
  const statusDiv = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const serverUrlInput = document.getElementById('serverUrl');
  
  // Load saved settings
  chrome.storage.sync.get(['captureEnabled', 'serverUrl'], function(result) {
    const enabled = result.captureEnabled || false;
    const serverUrl = result.serverUrl || 'http://localhost:8000';
    
    serverUrlInput.value = serverUrl;
    updateStatus(enabled);
  });
  
  // Toggle capture
  toggleBtn.addEventListener('click', function() {
    chrome.storage.sync.get(['captureEnabled'], function(result) {
      const enabled = result.captureEnabled || false;
      const newState = !enabled;
      
      chrome.storage.sync.set({
        captureEnabled: newState
      }, function() {
        updateStatus(newState);
      });
    });
  });
  
  // Save server URL
  serverUrlInput.addEventListener('change', function() {
    chrome.storage.sync.set({
      serverUrl: serverUrlInput.value
    });
  });
  
  // Test connection
  testBtn.addEventListener('click', function() {
    const serverUrl = serverUrlInput.value;
    
    fetch(`${serverUrl}/ping`)
      .then(response => response.json())
      .then(data => {
        alert('✓ Connection successful!');
      })
      .catch(error => {
        alert('✗ Connection failed!\n\nMake sure AutoPlay Seller app is running.');
      });
  });
  
  // Clear storage
  clearBtn.addEventListener('click', function() {
    if (confirm('Clear all stored comments?')) {
      chrome.storage.local.clear(function() {
        alert('Storage cleared!');
      });
    }
  });
  
  function updateStatus(enabled) {
    if (enabled) {
      statusDiv.className = 'status active';
      statusText.textContent = 'Active';
      toggleBtn.textContent = 'Stop Capture';
      toggleBtn.className = 'btn-danger';
    } else {
      statusDiv.className = 'status inactive';
      statusText.textContent = 'Inactive';
      toggleBtn.textContent = 'Start Capture';
      toggleBtn.className = 'btn-primary';
    }
  }
});
```

## Install Extension

1. Buat folder `tiktok-comment-capture`
2. Buat semua file di atas dalam folder tersebut
3. Buat icon sederhana (icon16.png, icon48.png, icon128.png) atau download dari internet
4. Buka Chrome/Edge
5. Ketik di address bar: `chrome://extensions/`
6. Enable "Developer mode"
7. Click "Load unpacked"
8. Pilih folder `tiktok-comment-capture`
9. Extension terpasang!

## Modify AutoPlay Seller untuk Terima HTTP Request

Tambahkan di `main.py`:

```python
from flask import Flask, request, jsonify
import threading

# Tambahkan di class AutoPlaySellerApp.__init__
def start_web_server(self):
    app = Flask(__name__)
    
    @app.route('/ping')
    def ping():
        return jsonify({'status': 'ok'})
    
    @app.route('/comment', methods=['POST'])
    def receive_comment():
        data = request.json
        username = data.get('username', 'unknown')
        text = data.get('text', '')
        
        # Create comment object
        comment = Comment(username, text)
        
        # Process via callback
        self.on_comment_received(comment)
        
        return jsonify({'status': 'ok', 'received': True})
    
    # Run in background thread
    threading.Thread(target=lambda: app.run(port=8000, debug=False), daemon=True).start()

# Call in __init__
self.start_web_server()
```

## Alternatif: Tanpa Extension

Jika tidak mau bikin extension, gunakan OCR untuk baca chat dari screen.

Install Tesseract OCR dan gunakan script di SETUP_GUIDE.md

---

**Note:** TikTok sering update struktur HTML mereka, jadi selector di `content.js` mungkin perlu di-update.
