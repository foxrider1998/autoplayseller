"""
Web Server untuk AutoPlay Seller
Control & preview video via browser (desktop & mobile)
"""
import os
import json
import time
from pathlib import Path
from threading import Thread, Lock
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from obs_controller import OBSController
from comment_detector import FileCommentDetector, CommentMatcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'autoplayseller-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
controller = None
detector = None
matcher = None
config = {}
monitoring = False
monitoring_thread = None
state_lock = Lock()

# App state
app_state = {
    'obs_connected': False,
    'monitoring': False,
    'main_video_playing': False,
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
    global monitoring
    
    add_log("Monitoring started", "success")
    
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
                        
                        # Play promo video
                        if controller.play_video(video_path, is_promo=True):
                            with state_lock:
                                app_state['current_promo'] = {
                                    'keyword': keyword,
                                    'video': Path(video_path).name,
                                    'comment': comment.text
                                }
                                app_state['total_videos_played'] += 1
                                app_state['total_comments_processed'] += 1
                            
                            # Emit update to clients
                            socketio.emit('video_playing', {
                                'keyword': keyword,
                                'video': Path(video_path).name,
                                'video_path': video_path,
                                'comment': comment.text
                            })
                        else:
                            add_log(f"✗ Failed to play video", "error")
                    else:
                        add_log(f"✗ Video not found: {video_path}", "error")
                else:
                    add_log(f"⚠ No match for: '{comment.text}'", "warning")
            
            time.sleep(config['comment_source'].get('check_interval', 1.0))
            
        except Exception as e:
            add_log(f"✗ Error: {str(e)}", "error")
            time.sleep(1)
    
    add_log("Monitoring stopped", "warning")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/mobile')
def mobile():
    """Mobile optimized page"""
    return render_template('mobile.html')

@app.route('/player')
def player():
    """Dedicated video player view"""
    return render_template('player.html')

@app.route('/api/status')
def get_status():
    """Get current status"""
    with state_lock:
        return jsonify(app_state)

@app.route('/api/config')
def get_config():
    """Get configuration"""
    main_video_name = ''
    if config['obs_settings'].get('main_video_path'):
        main_video_name = Path(config['obs_settings']['main_video_path']).name
    
    return jsonify({
        'keywords': list(config.get('comment_keywords', {}).keys()),
        'main_video': config['obs_settings'].get('main_video_path', ''),
        'main_video_name': main_video_name,
        'obs_host': config['obs_settings'].get('host', 'localhost'),
        'obs_port': config['obs_settings'].get('port', 4455),
        'return_to_main': config.get('video_settings', {}).get('return_to_main_video', True)
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
        config['obs_settings']['main_video_path'] = video_path
        
        # Save to file
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Update controller
        if controller:
            controller.main_video_path = video_path
            if controller.is_connected():
                controller.setup_main_video()
        
        add_log(f"✓ Main video updated: {Path(video_path).name}", "success")
        return jsonify({'success': True, 'message': 'Main video updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/connect', methods=['POST'])
def connect_obs():
    """Connect to OBS"""
    global controller
    
    try:
        if controller is None:
            controller = OBSController(config)
        
        if controller.auto_connect():
            with state_lock:
                app_state['obs_connected'] = True
            
            add_log("✓ Connected to OBS", "success")
            
            # Setup main video if configured
            if controller.main_video_path and Path(controller.main_video_path).exists():
                if controller.setup_main_video():
                    with state_lock:
                        app_state['main_video_playing'] = True
                    add_log("✓ Main video playing", "success")
            
            return jsonify({'success': True, 'message': 'Connected to OBS'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to OBS'}), 500
            
    except Exception as e:
        add_log(f"✗ Connection error: {str(e)}", "error")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect_obs():
    """Disconnect from OBS"""
    global controller
    
    if controller:
        controller.disconnect()
        with state_lock:
            app_state['obs_connected'] = False
            app_state['main_video_playing'] = False
        add_log("Disconnected from OBS", "warning")
    
    return jsonify({'success': True})

@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start monitoring comments"""
    global monitoring, monitoring_thread, detector, matcher
    
    if monitoring:
        return jsonify({'success': False, 'message': 'Already monitoring'})
    
    if not app_state['obs_connected']:
        return jsonify({'success': False, 'message': 'Connect to OBS first'}), 400
    
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

@app.route('/api/test-video', methods=['POST'])
def test_video():
    """Test play a specific video"""
    data = request.json
    keyword = data.get('keyword')
    
    if not keyword:
        return jsonify({'success': False, 'message': 'Keyword required'}), 400
    
    if not app_state['obs_connected']:
        return jsonify({'success': False, 'message': 'Connect to OBS first'}), 400
    
    keyword_data = config.get('comment_keywords', {}).get(keyword)
    if not keyword_data:
        return jsonify({'success': False, 'message': 'Keyword not found'}), 404
    
    video_path = keyword_data.get('video_path')
    if not video_path or not Path(video_path).exists():
        return jsonify({'success': False, 'message': 'Video not found'}), 404
    
    try:
        if controller.play_video(video_path, is_promo=True):
            add_log(f"🧪 Test playing: {Path(video_path).name}", "info")
            
            with state_lock:
                app_state['current_promo'] = {
                    'keyword': keyword,
                    'video': Path(video_path).name,
                    'comment': '[TEST]'
                }
            
            socketio.emit('video_playing', {
                'keyword': keyword,
                'video': Path(video_path).name,
                'video_path': video_path,
                'comment': '[TEST]'
            })
            
            return jsonify({'success': True, 'message': 'Video playing'})
        else:
            return jsonify({'success': False, 'message': 'Failed to play video'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/play-main', methods=['POST'])
def play_main_video():
    """Play main video"""
    if not app_state['obs_connected']:
        return jsonify({'success': False, 'message': 'Connect to OBS first'}), 400
    
    try:
        if controller.play_main_video():
            with state_lock:
                app_state['main_video_playing'] = True
                app_state['current_promo'] = None
            
            add_log("⏮ Returned to main video", "info")
            socketio.emit('main_video_playing', {})
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to play main video'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files"""
    # Try videos folder first
    videos_path = Path('videos')
    if videos_path.exists():
        video_file = videos_path / filename
        if video_file.exists():
            return send_from_directory('videos', filename)
    
    # Try absolute path (for main video outside videos folder)
    abs_path = Path(filename)
    if abs_path.exists():
        return send_from_directory(abs_path.parent, abs_path.name)
    
    return "Video not found", 404

@app.route('/api/video-url/<path:video_path>')
def get_video_url(video_path):
    """Get accessible URL for video file"""
    video_file = Path(video_path)
    
    if video_file.exists():
        # If in videos folder, use relative path
        try:
            rel_path = video_file.relative_to(Path.cwd() / 'videos')
            return jsonify({'url': f'/videos/{rel_path.as_posix()}'})
        except ValueError:
            # Outside videos folder, use filename only
            return jsonify({'url': f'/videos/{video_file.name}'})
    
    return jsonify({'url': None}), 404

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status_update', app_state)
    add_log("👤 Client connected", "info")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    add_log("👤 Client disconnected", "info")

def run_server(host='0.0.0.0', port=5000):
    """Run the web server"""
    global config
    
    print("=" * 60)
    print("🌐 AutoPlay Seller Web Server")
    print("=" * 60)
    
    # Load config
    config = load_config()
    print(f"✓ Configuration loaded")
    
    print(f"\n📱 Access URLs:")
    print(f"   Desktop: http://localhost:{port}/")
    print(f"   Mobile:  http://localhost:{port}/mobile")
    print(f"   Network: http://{get_local_ip()}:{port}/")
    print(f"   Mobile:  http://{get_local_ip()}:{port}/mobile")
    
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
