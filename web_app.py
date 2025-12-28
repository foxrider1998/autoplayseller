"""
Web Server untuk AutoPlay Seller - Simplified Version
Video plays directly in browser, no OBS connection needed
"""
import os
import json
import time
from pathlib import Path
from threading import Thread, Lock
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect
import requests
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from comment_detector import create_comment_detector, CommentMatcher
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'autoplayseller-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=500*1024*1024)

# Global state
detector = None
matcher = None
config = {}
monitoring = False
monitoring_thread = None
state_lock = Lock()

# App state
app_state = {
    'monitoring': False,
    'main_video_playing': True,
    'current_promo': None,
    'promo_queue': [],
    'total_comments_processed': 0,
    'total_videos_played': 0,
    'activity_log': []
}

# Cooldown map: video_path -> last trigger timestamp
promo_cooldowns = {}

def load_config():
    """Load configuration"""
    global config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def save_config():
    """Save configuration"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def add_log(message, level='info'):
    """Add log message to activity log"""
    with state_lock:
        timestamp = time.strftime('%H:%M:%S')
        app_state['activity_log'].insert(0, {
            'time': timestamp,
            'message': message,
            'level': level
        })
        # Keep last 50 logs
        app_state['activity_log'] = app_state['activity_log'][:50]
    
    # Emit to all connected clients
    socketio.emit('log_update', {
        'time': timestamp,
        'message': message,
        'level': level
    })

def monitoring_loop():
    """Background monitoring loop"""
    from urllib.parse import quote
    global monitoring
    
    add_log("📡 Monitoring started", "success")
    
    while monitoring:
        try:
            with state_lock:
                main_playing = app_state.get('main_video_playing', True)
            # Always pull new comments to broadcast
            comments = detector.get_new_comments()
            for comment in comments:
                # Broadcast comment to clients (mobile/player)
                socketio.emit('comment', {
                    'username': getattr(comment, 'username', ''),
                    'text': getattr(comment, 'text', ''),
                    'timestamp': getattr(comment, 'timestamp', '')
                })

                # Only attempt promo triggers when main video is playing
                if not main_playing:
                    continue

                # Find all matching keywords
                matches = []
                try:
                    matches = matcher.find_all_matches(comment.text)
                except Exception:
                    # Fallback to single match if API not available
                    k, cfg = matcher.find_match(comment.text)
                    if k and cfg:
                        matches = [(k, cfg)]

                if not matches:
                    add_log(f"⚠ No match for: '{comment.text}'", "warning")
                    continue

                add_log(f"📝 Comment: '{comment.text}'", "info")
                # Deduplicate by video_path and apply cooldown
                now_ts = time.time()
                seen = set()
                promo_items = []
                for keyword, cfg in matches:
                    vp = cfg.get('video_path')
                    if not vp or not Path(vp).exists():
                        add_log(f"✗ Video not found: {vp}", "error")
                        continue
                    if vp in seen:
                        continue
                    seen.add(vp)
                    last_ts = promo_cooldowns.get(vp, 0)
                    if last_ts and (now_ts - last_ts) < 60:
                        add_log(f"⏱ Cooldown active for {Path(vp).name} ({int(60 - (now_ts - last_ts))}s left)", "warning")
                        continue
                    promo_items.append({
                        'keyword': keyword,
                        'video_name': Path(vp).name,
                        'video_path': vp,
                        'comment': comment.text
                    })

                if not promo_items:
                    add_log("⚠ No eligible promos (cooldown or missing)", "warning")
                    continue

                # Play the first eligible, queue the rest
                first = promo_items[0]
                promo_cooldowns[first['video_path']] = now_ts
                with state_lock:
                    app_state['promo_queue'].extend(promo_items[1:])
                    app_state['current_promo'] = first
                    app_state['total_videos_played'] += 1
                    app_state['total_comments_processed'] += 1
                    app_state['main_video_playing'] = False

                add_log(f"🎯 Matched: '{first['keyword']}'", "success")
                add_log(f"▶ Playing: {first['video_name']}", "info")

                video_url = f"/video-absolute?path={quote(first['video_path'])}"
                socketio.emit('play_video', {
                    'keyword': first['keyword'],
                    'video_name': first['video_name'],
                    'video_url': video_url,
                    'comment': first['comment'],
                    'type': 'promo'
                })

            # Scan every second regardless
            time.sleep(1.0)
            
        except Exception as e:
            add_log(f"✗ Error: {str(e)}", "error")
            time.sleep(1)
    
    add_log("Monitoring stopped", "warning")

# ============ ROUTES ============

@app.route('/')
def index():
    """Redirect to admin"""
    return redirect('/admin')

@app.route('/admin')
def admin():
    """Admin control panel - Desktop only"""
    return render_template('admin.html')

@app.route('/player')
def player():
    """Dedicated video player view - Desktop/Browser"""
    return render_template('player_simple.html')

@app.route('/mobile')
def mobile():
    """Mobile video player view"""
    return render_template('mobile_player.html')

# ============ API ENDPOINTS ============

@app.route('/api/status')
def get_status():
    """Get current status"""
    with state_lock:
        return jsonify(app_state)

@app.route('/api/config')
def get_config():
    """Get configuration"""
    from urllib.parse import quote
    
    main_video_name = ''
    main_video_url = ''
    if config.get('obs_settings', {}).get('main_video_path'):
        main_video_path = config['obs_settings']['main_video_path']
        main_video_name = Path(main_video_path).name
        # Use absolute path endpoint
        main_video_url = f'/video-absolute?path={quote(main_video_path)}'
    
    keywords_list = []
    for keyword, data in config.get('comment_keywords', {}).items():
        video_path = data.get('video_path', '')
        video_url = ''
        if video_path:
            video_url = f'/video-absolute?path={quote(video_path)}'
        
        keywords_list.append({
            'keyword': keyword,
            'video_path': video_path,
            'video_url': video_url,
            'video_name': Path(video_path).name if video_path else '',
            'response_text': data.get('response_text', ''),
            'is_regex': data.get('is_regex', False)
        })
    
    return jsonify({
        'keywords': keywords_list,
        'main_video': config.get('obs_settings', {}).get('main_video_path', ''),
        'main_video_name': main_video_name,
        'main_video_url': main_video_url,
        'return_to_main': config.get('video_settings', {}).get('return_to_main_video', True),
        'comment_source': config.get('comment_source', {
            'type': 'file',
            'file_path': 'comments.txt',
            'check_interval': 1.0
        }),
        'tiktok_oauth': config.get('tiktok_oauth', {})
    })

@app.route('/api/update-main-video', methods=['POST'])
def update_main_video():
    """Update main video path"""
    data = request.json
    video_path = data.get('video_path')
    
    if not video_path:
        return jsonify({'success': False, 'message': 'Video path required'}), 400
    
    if not Path(video_path).exists():
        return jsonify({'success': False, 'message': 'Video file not found'}), 404
    
    try:
        # Update config
        if 'obs_settings' not in config:
            config['obs_settings'] = {}
        
        config['obs_settings']['main_video_path'] = video_path
        save_config()
        
        # Notify all players to play main video
        socketio.emit('play_video', {
            'video': Path(video_path).name,
            'video_path': video_path,
            'type': 'main'
        })
        
        with state_lock:
            app_state['main_video_playing'] = True
            app_state['current_promo'] = None
        
        add_log(f"✓ Main video updated: {Path(video_path).name}", "success")
        return jsonify({'success': True, 'message': 'Main video updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keyword/add', methods=['POST'])
def add_keyword():
    """Add new keyword"""
    data = request.json
    keyword = data.get('keyword', '').strip()
    video_path = data.get('video_path', '').strip()
    response_text = data.get('response_text', '').strip()
    is_regex = data.get('is_regex', False)
    
    if not keyword:
        return jsonify({'success': False, 'message': 'Keyword required'}), 400
    
    if keyword in config.get('comment_keywords', {}):
        return jsonify({'success': False, 'message': 'Keyword already exists'}), 400
    
    try:
        if 'comment_keywords' not in config:
            config['comment_keywords'] = {}
        
        config['comment_keywords'][keyword] = {
            'video_path': video_path,
            'response_text': response_text or f"Terima kasih! {keyword} akan kami proses segera 🎉",
            'is_regex': is_regex
        }
        
        save_config()
        
        # Reload matcher
        global matcher
        matcher = CommentMatcher(config.get('comment_keywords', {}))
        
        add_log(f"✓ Added keyword: '{keyword}'", "success")
        return jsonify({'success': True, 'message': 'Keyword added'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keyword/update', methods=['POST'])
def update_keyword():
    """Update existing keyword"""
    data = request.json
    old_keyword = data.get('old_keyword', '').strip()
    new_keyword = data.get('keyword', '').strip()
    video_path = data.get('video_path', '').strip()
    response_text = data.get('response_text', '').strip()
    is_regex = data.get('is_regex', False)
    
    if not old_keyword or not new_keyword:
        return jsonify({'success': False, 'message': 'Keywords required'}), 400
    
    try:
        if old_keyword not in config.get('comment_keywords', {}):
            return jsonify({'success': False, 'message': 'Keyword not found'}), 404
        
        # If keyword changed, delete old and create new
        if old_keyword != new_keyword:
            if new_keyword in config['comment_keywords']:
                return jsonify({'success': False, 'message': 'New keyword already exists'}), 400
            
            del config['comment_keywords'][old_keyword]
        
        config['comment_keywords'][new_keyword] = {
            'video_path': video_path,
            'response_text': response_text,
            'is_regex': is_regex
        }
        
        save_config()
        
        # Reload matcher
        global matcher
        matcher = CommentMatcher(config.get('comment_keywords', {}))
        
        add_log(f"✓ Updated keyword: '{new_keyword}'", "success")
        return jsonify({'success': True, 'message': 'Keyword updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keyword/delete', methods=['POST'])
def delete_keyword():
    """Delete keyword"""
    data = request.json
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'success': False, 'message': 'Keyword required'}), 400
    
    try:
        if keyword not in config.get('comment_keywords', {}):
            return jsonify({'success': False, 'message': 'Keyword not found'}), 404
        
        del config['comment_keywords'][keyword]
        save_config()
        
        # Reload matcher
        global matcher
        matcher = CommentMatcher(config.get('comment_keywords', {}))
        
        add_log(f"✓ Deleted keyword: '{keyword}'", "success")
        return jsonify({'success': True, 'message': 'Keyword deleted'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start monitoring comments"""
    global monitoring, monitoring_thread, detector, matcher
    
    if monitoring:
        return jsonify({'success': False, 'message': 'Already monitoring'})
    
    try:
        # Initialize detector and matcher according to source type
        detector = create_comment_detector(config)
        try:
            detector.start()
        except Exception:
            pass
        matcher = CommentMatcher(config.get('comment_keywords', {}))
        
        monitoring = True
        with state_lock:
            app_state['monitoring'] = True
        
        monitoring_thread = Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        return jsonify({'success': True, 'message': 'Monitoring started'})
        
    except Exception as e:
        add_log(f"✗ Failed to start monitoring: {str(e)}", "error")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop monitoring comments"""
    global monitoring
    
    monitoring = False
    with state_lock:
        app_state['monitoring'] = False
    
    return jsonify({'success': True, 'message': 'Monitoring stopped'})

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    """Handle video upload and return saved path"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400

        filename = secure_filename(file.filename)
        videos_dir = Path('videos')
        videos_dir.mkdir(parents=True, exist_ok=True)

        save_path = videos_dir / filename
        file.save(str(save_path))

        # Return relative path so it works on Windows paths too
        return jsonify({'success': True, 'path': str(save_path)})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-video', methods=['POST'])
def test_video():
    """Test play a specific video"""
    from urllib.parse import quote
    
    data = request.json
    keyword = data.get('keyword')
    
    if not keyword:
        return jsonify({'success': False, 'message': 'Keyword required'}), 400
    
    keyword_data = config.get('comment_keywords', {}).get(keyword)
    if not keyword_data:
        return jsonify({'success': False, 'message': 'Keyword not found'}), 404
    
    video_path = keyword_data.get('video_path')
    if not video_path or not Path(video_path).exists():
        return jsonify({'success': False, 'message': 'Video not found'}), 404
    
    try:
        add_log(f"🧪 Test playing: {Path(video_path).name}", "info")
        
        video_url = f'/video-absolute?path={quote(video_path)}'
        
        with state_lock:
            app_state['current_promo'] = {
                'keyword': keyword,
                'video': Path(video_path).name,
                'video_path': video_path,
                'comment': '[TEST]'
            }
            app_state['main_video_playing'] = False
        
        socketio.emit('play_video', {
            'keyword': keyword,
            'video_name': Path(video_path).name,
            'video_url': video_url,
            'comment': '[TEST]',
            'type': 'promo'
        })
        
        return jsonify({'success': True, 'message': 'Video playing'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/play-main', methods=['POST'])
def play_main_video():
    """Play main video"""
    from urllib.parse import quote
    
    main_video = config.get('obs_settings', {}).get('main_video_path', '')
    
    if not main_video or not Path(main_video).exists():
        return jsonify({'success': False, 'message': 'Main video not configured'}), 400
    
    try:
        video_url = f'/video-absolute?path={quote(main_video)}'
        
        with state_lock:
            app_state['main_video_playing'] = True
            app_state['current_promo'] = None
        
        socketio.emit('play_video', {
            'video_name': Path(main_video).name,
            'video_url': video_url,
            'type': 'main'
        })
        
        add_log("⏮ Returned to main video", "info")
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/update-platform', methods=['POST'])
def update_platform():
    """Update live platform configuration"""
    try:
        data = request.json
        platform_type = data.get('type', 'file')

        # Prepare platform config
        platform_config = {
            'type': platform_type
        }

        if platform_type == 'file':
            platform_config['file_path'] = data.get('file_path', 'comments.txt')
            platform_config['check_interval'] = data.get('check_interval', 1.0)
        elif platform_type == 'tiktok':
            # TikTok Research API config
            platform_config['token_env'] = data.get('token_env') or ''
            platform_config['access_token'] = data.get('access_token') or ''
            platform_config['video_id'] = int(data.get('video_id', 0))
            platform_config['fields'] = data.get('fields') or 'id,text,like_count,reply_count,create_time,video_id,parent_comment_id'
            platform_config['max_count'] = int(data.get('max_count', 10))
            platform_config['cursor'] = int(data.get('cursor', 0))
            platform_config['poll_interval'] = float(data.get('poll_interval', 2.0))
            # OAuth helpers (optional)
            platform_config['client_key'] = data.get('client_key') or ''
            platform_config['redirect_uri'] = data.get('redirect_uri') or ''
            platform_config['scope'] = data.get('scope') or ''
        elif platform_type == 'tiktok_dummy':
            # Dummy TikTok comments config
            platform_config['poll_interval'] = float(data.get('poll_interval', 1.0))
        elif platform_type == 'tiktok_live':
            # TikTok Live Connector config
            platform_config['live_username'] = data.get('live_username') or data.get('username') or ''
            platform_config['poll_interval'] = float(data.get('poll_interval', 1.0))
            platform_config['bridge_path'] = data.get('bridge_path') or str(Path('node_bridge') / 'tiktok_live_bridge.js')
        elif platform_type == 'tiktok_live_socket':
            # External Socket.IO TikTok Live server
            platform_config['server_url'] = data.get('server_url') or 'http://localhost:8081'
            platform_config['live_username'] = data.get('live_username') or data.get('username') or ''
            platform_config['poll_interval'] = float(data.get('poll_interval', 1.0))
        elif platform_type == 'tiktok_live_py':
            # Python TikTokLive client
            platform_config['live_username'] = data.get('live_username') or data.get('username') or ''
            platform_config['poll_interval'] = float(data.get('poll_interval', 1.0))
        else:
            # Unknown/custom platforms placeholder
            platform_config['check_interval'] = data.get('check_interval', 1.0)
        
        # Update config
        config['comment_source'] = platform_config
        save_config()
        
        # Update app state
        with state_lock:
            app_state['config'] = config
        
        add_log(f"✅ Platform configuration updated: {platform_type}", "success")
        
        # Restart monitoring if active
        if app_state.get('monitoring'):
            socketio.emit('log_update', {
                'timestamp': datetime.now().isoformat(),
                'message': '🔄 Restarting monitoring with new platform config...',
                'level': 'info'
            })
            # Note: actual restart would happen in comment_detector
        
        return jsonify({
            'success': True,
            'message': f'Platform configuration updated to {platform_type}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-tiktok', methods=['POST'])
def test_tiktok():
    """Test TikTok Research API configuration by fetching a page of comments"""
    try:
        src = request.json or {}
        from tiktok_api import fetch_video_comments
        result = fetch_video_comments(
            src or config.get('comment_source', {}),
            video_id=int(src.get('video_id') or config.get('comment_source', {}).get('video_id', 0)),
            fields=src.get('fields') or config.get('comment_source', {}).get('fields', 'id,text'),
            max_count=int(src.get('max_count') or config.get('comment_source', {}).get('max_count', 10)),
            cursor=int(src.get('cursor') or config.get('comment_source', {}).get('cursor', 0)),
        )
        count = len(result.get('comments', []))
        return jsonify({'success': True, 'message': f'Fetched {count} comments', 'has_more': result.get('has_more', False)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/tiktok-auth-url', methods=['POST'])
def tiktok_auth_url():
    """Build TikTok OAuth authorize URL from provided inputs."""
    try:
        body = request.json or {}
        client_key = (body.get('client_key') or '').strip()
        redirect_uri = (body.get('redirect_uri') or '').strip()
        scope_in = (body.get('scope') or '').strip()
        state = (body.get('state') or 'state').strip()
        if not client_key or not redirect_uri:
            return jsonify({'success': False, 'message': 'client_key and redirect_uri are required'}), 400
        # Normalize scope: accept comma or space separated, output space-delimited as commonly used
        scopes = [s.strip() for s in scope_in.replace(',', ' ').split() if s.strip()]
        scope_param = ' '.join(scopes)
        from urllib.parse import urlencode, quote
        params = {
            'client_key': client_key,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': scope_param,
            'state': state,
        }
        # urlencode will encode spaces as +; TikTok accepts standard encoding
        query = urlencode(params, safe=':/')
        url = f"https://www.tiktok.com/v2/auth/authorize/?{query}"
        return jsonify({'success': True, 'url': url})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/oauth/callback')
def oauth_callback():
    """Simple callback helper that shows received code/state for manual exchange."""
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    html = f"""
    <html><body style='font-family:system-ui;padding:24px;'>
      <h2>TikTok OAuth Callback</h2>
      <p><b>code:</b> {code}</p>
      <p><b>state:</b> {state}</p>
      <p>Copy the code into Admin → TikTok OAuth → Exchange Code.</p>
    </body></html>
    """
    return html

@app.route('/api/tiktok/exchange-code', methods=['POST'])
def tiktok_exchange_code():
    """Exchange authorization code for access/refresh tokens and persist them."""
    try:
        body = request.json or {}
        client_key = (body.get('client_key') or '').strip()
        client_secret = (body.get('client_secret') or '').strip()
        code = (body.get('code') or '').strip()
        if not client_key or not client_secret or not code:
            return jsonify({'success': False, 'message': 'client_key, client_secret, and code are required'}), 400
        params = {
            'client_key': client_key,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
        }
        url = 'https://open-api.tiktok.com/oauth/access_token/'
        r = requests.post(url, params=params, timeout=20)
        data = r.json()
        if r.status_code != 200 or (data.get('message') == 'error'):
            return jsonify({'success': False, 'message': data}), 400
        token_data = data.get('data', {})
        # Persist
        config['tiktok_oauth'] = {
            'open_id': token_data.get('open_id'),
            'scope': token_data.get('scope'),
            'access_token': token_data.get('access_token'),
            'expires_in': token_data.get('expires_in'),
            'refresh_token': token_data.get('refresh_token'),
            'refresh_expires_in': token_data.get('refresh_expires_in'),
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        save_config()
        return jsonify({'success': True, 'data': config['tiktok_oauth']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/tiktok/refresh-token', methods=['POST'])
def tiktok_refresh_token():
    """Refresh access token with refresh_token and persist new values."""
    try:
        body = request.json or {}
        client_key = (body.get('client_key') or '').strip()
        refresh_token = (body.get('refresh_token') or config.get('tiktok_oauth', {}).get('refresh_token') or '').strip()
        if not client_key or not refresh_token:
            return jsonify({'success': False, 'message': 'client_key and refresh_token are required'}), 400
        params = {
            'client_key': client_key,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        url = 'https://open-api.tiktok.com/oauth/refresh_token/'
        r = requests.post(url, params=params, timeout=20)
        data = r.json()
        if r.status_code != 200 or (data.get('message') == 'error'):
            return jsonify({'success': False, 'message': data}), 400
        token_data = data.get('data', {})
        # Persist (note refresh_token may rotate)
        config['tiktok_oauth'] = {
            'open_id': token_data.get('open_id'),
            'scope': token_data.get('scope'),
            'access_token': token_data.get('access_token'),
            'expires_in': token_data.get('expires_in'),
            'refresh_token': token_data.get('refresh_token'),
            'refresh_expires_in': token_data.get('refresh_expires_in'),
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        save_config()
        return jsonify({'success': True, 'data': config['tiktok_oauth']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/tiktok/revoke', methods=['POST'])
def tiktok_revoke():
    """Revoke access for a user (open_id + access_token)."""
    try:
        body = request.json or {}
        open_id = (body.get('open_id') or config.get('tiktok_oauth', {}).get('open_id') or '').strip()
        access_token = (body.get('access_token') or config.get('tiktok_oauth', {}).get('access_token') or '').strip()
        if not open_id or not access_token:
            return jsonify({'success': False, 'message': 'open_id and access_token are required'}), 400
        params = {
            'open_id': open_id,
            'access_token': access_token,
        }
        url = 'https://open-api.tiktok.com/oauth/revoke/'
        r = requests.post(url, params=params, timeout=20)
        data = r.json()
        if r.status_code != 200 or (data.get('message') == 'error'):
            return jsonify({'success': False, 'message': data}), 400
        # Clear stored tokens
        config['tiktok_oauth'] = {}
        save_config()
        return jsonify({'success': True, 'data': data.get('data', {})})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-platform', methods=['POST'])
def test_platform():
    """Test live platform connection"""
    try:
        data = request.json
        platform_type = data.get('type')
        
        platform_names = {
            'tiktokshop': 'TikTok Shop Live',
            'shopee': 'Shopee Live',
            'tokopedia': 'Tokopedia Play',
            'bukalapak': 'Bukalapak Live',
            'lazada': 'Lazada Live',
            'jdid': 'JD.ID Live',
            'blibli': 'Blibli Live'
        }
        
        platform_name = platform_names.get(platform_type, platform_type)
        
        # Simulate connection test (actual implementation would call platform APIs)
        # For now, just validate credentials are present
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username dan Password diperlukan'
            })
        
        # TODO: Implement actual API calls for each platform
        # This is placeholder for future implementation
        return jsonify({
            'success': True,
            'message': f'Koneksi ke {platform_name} akan diimplementasikan.\n\n' +
                      f'Username: {username}\n' +
                      f'Platform: {platform_name}\n\n' +
                      'Note: Integrasi API memerlukan kredensial resmi dari platform.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/video/<path:filename>')
def serve_video(filename):
    """Serve video files from anywhere"""
    from urllib.parse import unquote
    
    # Decode filename
    filename = unquote(filename)
    
    # Try to find video file
    # 1. Check in videos folder
    videos_path = Path('videos') / filename
    if videos_path.exists():
        return send_from_directory('videos', filename)
    
    # 2. Check in config for absolute path
    for keyword_data in config.get('comment_keywords', {}).values():
        video_path = Path(keyword_data.get('video_path', ''))
        if video_path.name == filename and video_path.exists():
            return send_from_directory(str(video_path.parent), video_path.name)
    
    # 3. Check main video
    main_video = Path(config.get('obs_settings', {}).get('main_video_path', ''))
    if main_video.name == filename and main_video.exists():
        return send_from_directory(str(main_video.parent), main_video.name)
    
    return "Video not found", 404

@app.route('/video-absolute')
def serve_video_absolute():
    """Serve video from absolute path"""
    video_path = request.args.get('path', '')
    
    if not video_path:
        return "No path specified", 400
    
    video_file = Path(video_path)
    
    if not video_file.exists():
        return f"Video not found: {video_path}", 404
    
    if not video_file.is_file():
        return "Not a file", 400
    
    # Serve from parent directory
    return send_from_directory(
        str(video_file.parent.absolute()), 
        video_file.name,
        mimetype='video/mp4'
    )

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status_update', app_state)
    add_log("👤 Client connected", "info")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    add_log("👤 Client disconnected", "info")

@socketio.on('video_ended')
def handle_video_ended(data):
    """Handle video ended event from player"""
    video_type = data.get('type', 'promo')
    
    if video_type == 'promo':
        # If there is a queued promo, play next; otherwise return to main
        from urllib.parse import quote
        next_item = None
        with state_lock:
            if app_state['promo_queue']:
                next_item = app_state['promo_queue'].pop(0)
                app_state['current_promo'] = next_item
        if next_item:
            add_log(f"⏭ Next promo: {next_item['video_name']}", "info")
            video_url = f"/video-absolute?path={quote(next_item['video_path'])}"
            socketio.emit('play_video', {
                'keyword': next_item.get('keyword'),
                'video_name': next_item['video_name'],
                'video_url': video_url,
                'comment': next_item.get('comment', ''),
                'type': 'promo'
            })
        else:
            # Return to main video
            main_video = config.get('obs_settings', {}).get('main_video_path', '')
            if main_video and Path(main_video).exists():
                time.sleep(1)  # Small delay
                
                with state_lock:
                    app_state['main_video_playing'] = True
                    app_state['current_promo'] = None
                
                socketio.emit('play_video', {
                    'video_name': Path(main_video).name,
                    'video_url': f'/video-absolute?path={quote(main_video)}',
                    'type': 'main'
                })
                
                add_log("⏮ Auto-returned to main video", "info")

def run_server(host='0.0.0.0', port=5000):
    """Run the web server"""
    global config
    
    print("=" * 60)
    print("🌐 AutoPlay Seller Web Server (Simplified)")
    print("=" * 60)
    
    # Load config
    config = load_config()
    print(f"✓ Configuration loaded")
    
    print(f"\n📱 Access URLs:")
    print(f"   Admin Panel:  http://localhost:{port}/")
    print(f"   Video Player: http://localhost:{port}/player")
    print(f"   Mobile Admin: http://localhost:{port}/mobile")
    print(f"\n   Network Access:")
    print(f"   Admin:  http://{get_local_ip()}:{port}/")
    print(f"   Player: http://{get_local_ip()}:{port}/player")
    
    print(f"\n💡 Workflow:")
    print(f"   1. Open Admin Panel untuk control")
    print(f"   2. Open Video Player di browser/OBS untuk display")
    print(f"   3. Player akan auto-play video sesuai comment")
    
    print(f"\n🚀 Starting server on {host}:{port}...")
    print(f"   Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

if __name__ == '__main__':
    run_server()
