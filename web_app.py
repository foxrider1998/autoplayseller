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
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
from comment_detector import FileCommentDetector, CommentMatcher

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
    'total_comments_processed': 0,
    'total_videos_played': 0,
    'activity_log': []
}

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
            # Check for new comments
            comments = detector.get_new_comments()
            
            for comment in comments:
                # Find matching keyword
                keyword, config_data = matcher.find_match(comment.text)
                
                if keyword and config_data:
                    video_path = config_data.get('video_path')
                    
                    if video_path and Path(video_path).exists():
                        add_log(f"📝 Comment: '{comment.text}'", "info")
                        add_log(f"🎯 Matched: '{keyword}'", "success")
                        add_log(f"▶ Playing: {Path(video_path).name}", "info")
                        
                        # Create video URL
                        video_url = f'/video-absolute?path={quote(video_path)}'
                        
                        # Trigger video play on all clients
                        with state_lock:
                            app_state['current_promo'] = {
                                'keyword': keyword,
                                'video': Path(video_path).name,
                                'video_path': video_path,
                                'comment': comment.text
                            }
                            app_state['total_videos_played'] += 1
                            app_state['total_comments_processed'] += 1
                            app_state['main_video_playing'] = False
                        
                        # Emit to all players
                        socketio.emit('play_video', {
                            'keyword': keyword,
                            'video_name': Path(video_path).name,
                            'video_url': video_url,
                            'comment': comment.text,
                            'type': 'promo'
                        })
                    else:
                        add_log(f"✗ Video not found: {video_path}", "error")
                else:
                    add_log(f"⚠ No match for: '{comment.text}'", "warning")
            
            time.sleep(config['comment_source'].get('check_interval', 1.0))
            
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
        })
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
        matcher = CommentMatcher(config)
        
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
        matcher = CommentMatcher(config)
        
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
        matcher = CommentMatcher(config)
        
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
        # Initialize detector and matcher
        detector = FileCommentDetector(config)
        matcher = CommentMatcher(config)
        
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
            'type': platform_type,
            'check_interval': data.get('check_interval', 1.0)
        }
        
        if platform_type == 'file':
            platform_config['file_path'] = data.get('file_path', 'comments.txt')
        else:
            # Live platform credentials
            platform_config['username'] = data.get('username', '')
            platform_config['password'] = data.get('password', '')
            platform_config['api_key'] = data.get('api_key', '')
            platform_config['room_id'] = data.get('room_id', '')
        
        # Update config
        config['comment_source'] = platform_config
        save_config()
        
        # Update app state
        with state_lock:
            app_state['config'] = config
        
        add_log(f"✅ Platform configuration updated: {platform_type}", "success")
        
        # Restart monitoring if active
        if app_state.get('monitoring_active'):
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
        # Return to main video
        main_video = config.get('obs_settings', {}).get('main_video_path', '')
        if main_video and Path(main_video).exists():
            time.sleep(1)  # Small delay
            
            with state_lock:
                app_state['main_video_playing'] = True
                app_state['current_promo'] = None
            
            socketio.emit('play_video', {
                'video': Path(main_video).name,
                'video_path': main_video,
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
