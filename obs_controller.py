"""
OBS Controller Module
Kontrol OBS Studio via WebSocket untuk autoplay video
"""
import json
import time
import psutil
import socket
from pathlib import Path
from typing import Optional, Dict, List, Tuple
try:
    from obswebsocket import obsws, requests as obs_requests
except ImportError:
    print("Warning: obs-websocket-py not installed. Run: pip install obs-websocket-py")
    obsws = None
    obs_requests = None


class OBSController:
    """Controller untuk OBS Studio via WebSocket"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.obs_config = config['obs_settings']
        self.video_settings = config.get('video_settings', {})
        
        self.host = self.obs_config.get('host', 'localhost')
        self.port = self.obs_config.get('port', 4455)
        self.password = self.obs_config.get('password', '')
        self.video_source_name = self.obs_config.get('video_source_name', 'VideoPlayer')
        self.scene_name = self.obs_config.get('scene_name', 'Main Scene')
        
        # Main/background video settings
        self.main_video_source = self.obs_config.get('main_video_source', 'MainVideo')
        self.main_video_path = self.obs_config.get('main_video_path', '')
        self.return_to_main = self.video_settings.get('return_to_main_video', True)
        self.main_video_delay = self.video_settings.get('main_video_delay', 1.0)
        
        self.ws: Optional[obsws] = None
        self.connected = False
        self.current_video = None
        self.is_playing_promo = False
    
    def is_obs_running(self) -> bool:
        """Check apakah OBS Studio sedang running"""
        obs_process_names = ['obs64.exe', 'obs32.exe', 'obs.exe', 'OBS.exe']
        
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in obs_process_names:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
    
    def detect_obs_websocket(self) -> Optional[Tuple[str, int]]:
        """
        Auto-detect OBS WebSocket server
        Returns (host, port) jika ditemukan, None jika tidak
        """
        # Common ports untuk OBS WebSocket
        common_ports = [4455, 4444, 4567, 4568]
        
        for port in common_ports:
            if self._test_connection('localhost', port):
                return ('localhost', port)
        
        # Try 127.0.0.1 juga
        for port in common_ports:
            if self._test_connection('127.0.0.1', port):
                return ('127.0.0.1', port)
        
        return None
    
    def _test_connection(self, host: str, port: int, timeout: float = 0.5) -> bool:
        """Test apakah port terbuka"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def auto_connect(self) -> bool:
        """
        Auto-detect dan connect ke OBS
        Returns True jika berhasil connect
        """
        if not obsws:
            print("ERROR: obs-websocket-py not installed!")
            return False
        
        # Check apakah OBS running
        print("🔍 Checking if OBS is running...")
        if not self.is_obs_running():
            print("✗ OBS Studio is not running!")
            print("  Please start OBS Studio first.")
            return False
        
        print("✓ OBS Studio is running")
        
        # Detect WebSocket
        print("🔍 Detecting OBS WebSocket server...")
        detected = self.detect_obs_websocket()
        
        if detected:
            host, port = detected
            print(f"✓ Found OBS WebSocket at {host}:{port}")
            
            # Update config dengan detected values
            self.host = host
            self.port = port
            
            # Try connect
            return self.connect()
        else:
            print("✗ Could not detect OBS WebSocket server")
            print("  Make sure WebSocket server is enabled in OBS:")
            print("  Tools → WebSocket Server Settings → Enable WebSocket server")
            print(f"  Trying default connection ({self.host}:{self.port})...")
            return self.connect()
    
    def connect(self) -> bool:
        """Koneksi ke OBS WebSocket"""
        if not obsws:
            print("ERROR: obs-websocket-py not installed!")
            return False
        
        try:
            print(f"Connecting to OBS at {self.host}:{self.port}...")
            
            # Create WebSocket connection with empty password
            self.ws = obsws(self.host, self.port, self.password if self.password else '')
            
            # Connect with timeout
            self.ws.connect()
            
            self.connected = True
            print("✓ Connected to OBS successfully!")
            
            # Get OBS version info
            try:
                version_info = self.ws.call(obs_requests.GetVersion())
                print(f"  OBS Studio Version: {version_info.getObsVersion()}")
                print(f"  WebSocket Version: {version_info.getWebsocketVersion()}")
            except:
                # Version call failed but connection OK
                print("  (Version info unavailable)")
            
            return True
            
        except ConnectionRefusedError:
            print(f"✗ Connection refused on port {self.port}")
            print(f"  Make sure WebSocket server is enabled in OBS:")
            print(f"  Tools → WebSocket Server Settings → Enable WebSocket server")
            self.connected = False
            return False
            
        except TimeoutError:
            print(f"✗ Connection timeout on port {self.port}")
            print(f"  OBS may be running but WebSocket not responding")
            self.connected = False
            return False
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Failed to connect to OBS: {error_msg}")
            
            # Specific error messages
            if "authentication" in error_msg.lower() or "password" in error_msg.lower():
                print(f"  → Password required! Set password in config.json")
            elif "refused" in error_msg.lower():
                print(f"  → Port {self.port} not accepting connections")
                print(f"  → Enable WebSocket in OBS: Tools → WebSocket Server Settings")
            else:
                print(f"  Make sure:")
                print(f"  1. OBS Studio is running")
                print(f"  2. WebSocket server is enabled (Tools → WebSocket Server Settings)")
                print(f"  3. Port is {self.port} (default: 4455)")
            
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect dari OBS"""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
                print("Disconnected from OBS")
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    def is_connected(self) -> bool:
        """Check apakah masih terkoneksi"""
        return self.connected and self.ws is not None
    
    def get_scenes(self) -> list:
        """Get daftar scene di OBS"""
        if not self.is_connected():
            return []
        
        try:
            response = self.ws.call(obs_requests.GetSceneList())
            scenes = response.getScenes()
            return [scene['sceneName'] for scene in scenes]
        except Exception as e:
            print(f"Error getting scenes: {e}")
            return []
    
    def get_sources(self, scene_name: str = None) -> list:
        """Get daftar source di scene"""
        if not self.is_connected():
            return []
        
        scene = scene_name or self.scene_name
        
        try:
            response = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene))
            # Try different response methods
            try:
                items = response.getSceneItems()
            except:
                items = response.datain.get('sceneItems', [])
            
            return [item['sourceName'] for item in items]
        except Exception as e:
            # Silently return empty list if scene has no items
            return []
    
    def set_source_visibility(self, source_name: str, visible: bool, scene_name: str = None):
        """Set visibility dari source"""
        if not self.is_connected():
            return False
        
        scene = scene_name or self.scene_name
        
        try:
            # Get scene item ID
            response = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene))
            items = response.getSceneItems()
            
            source_id = None
            for item in items:
                if item['sourceName'] == source_name:
                    source_id = item['sceneItemId']
                    break
            
            if source_id is None:
                print(f"Source '{source_name}' not found in scene '{scene}'")
                return False
            
            # Set visibility
            self.ws.call(obs_requests.SetSceneItemEnabled(
                sceneName=scene,
                sceneItemId=source_id,
                sceneItemEnabled=visible
            ))
            
            return True
        except Exception as e:
            print(f"Error setting source visibility: {e}")
            return False
    
    def create_media_source(self, source_name: str, video_path: str, scene_name: str = None, looping: bool = False):
        """Buat media source untuk video"""
        if not self.is_connected():
            return False
        
        scene = scene_name or self.scene_name
        
        try:
            # Create input (source)
            settings = {
                'local_file': str(Path(video_path).absolute()),
                'looping': looping,
                'restart_on_activate': True,
                'close_when_inactive': False
            }
            
            self.ws.call(obs_requests.CreateInput(
                sceneName=scene,
                inputName=source_name,
                inputKind='ffmpeg_source',
                inputSettings=settings,
                sceneItemEnabled=False
            ))
            
            print(f"Created media source: {source_name} (looping={looping})")
            return True
        except Exception as e:
            print(f"Error creating media source: {e}")
            return False
    
    def update_media_source(self, source_name: str, video_path: str, looping: bool = False):
        """Update media source dengan video baru"""
        if not self.is_connected():
            return False
        
        try:
            video_abs_path = str(Path(video_path).absolute())
            
            # Update input settings
            self.ws.call(obs_requests.SetInputSettings(
                inputName=source_name,
                inputSettings={
                    'local_file': video_abs_path,
                    'looping': looping,
                    'restart_on_activate': True
                },
                overlay=True
            ))
            
            print(f"Updated media source '{source_name}' with: {video_path} (looping={looping})")
            return True
        except Exception as e:
            print(f"Error updating media source: {e}")
            return False
    
    def play_video(self, video_path: str, source_name: str = None, is_promo: bool = True):
        """Play video di OBS"""
        if not self.is_connected():
            print("Not connected to OBS!")
            return False
        
        source = source_name or self.video_source_name
        video_file = Path(video_path)
        
        # Check if video exists
        if not video_file.exists():
            print(f"✗ Video file not found: {video_path}")
            return False
        
        print(f"\n▶ Playing {'PROMO' if is_promo else 'MAIN'} video: {video_file.name}")
        
        try:
            # Check if source exists, create if not
            sources = self.get_sources()
            if source not in sources:
                print(f"  → Media source '{source}' not found, creating...")
                if not self.create_media_source(source, video_path, looping=not is_promo):
                    print(f"  ✗ Failed to create media source!")
                    return False
                print(f"  ✓ Media source created!")
            
            # Update source dengan video baru
            self.update_media_source(source, video_path, looping=not is_promo)
            
            # Show source
            self.set_source_visibility(source, True)
            
            # Trigger media restart
            self.ws.call(obs_requests.TriggerMediaInputAction(
                inputName=source,
                mediaAction='OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART'
            ))
            
            self.current_video = video_path
            self.is_playing_promo = is_promo
            
            print(f"✓ Video playing!")
            
            # If promo video, schedule return to main
            if is_promo and self.return_to_main and self.main_video_path:
                import threading
                duration = self.get_media_duration(source)
                if duration > 0:
                    def return_to_main():
                        time.sleep(duration + self.main_video_delay)
                        if self.is_playing_promo:  # Only if still playing promo
                            print(f"\n⏮ Returning to main video...")
                            self.play_main_video()
                    
                    thread = threading.Thread(target=return_to_main, daemon=True)
                    thread.start()
            
            return True
        except Exception as e:
            print(f"✗ Error playing video: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_video(self, source_name: str = None):
        """Stop video playback"""
        if not self.is_connected():
            return False
        
        source = source_name or self.video_source_name
        
        try:
            # Stop media
            self.ws.call(obs_requests.TriggerMediaInputAction(
                inputName=source,
                mediaAction='OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP'
            ))
            
            # Hide source if configured
            if self.video_settings.get('auto_hide_after_play', True):
                self.set_source_visibility(source, False)
            
            self.current_video = None
            print("Video stopped")
            return True
        except Exception as e:
            print(f"Error stopping video: {e}")
            return False
    
    def get_media_duration(self, source_name: str = None) -> float:
        """Get durasi video (dalam detik)"""
        if not self.is_connected():
            return 0
        
        source = source_name or self.video_source_name
        
        try:
            response = self.ws.call(obs_requests.GetMediaInputStatus(inputName=source))
            duration = response.getMediaDuration()
            return duration / 1000.0  # Convert ms to seconds
        except Exception as e:
            print(f"Error getting media duration: {e}")
            return 0
    
    def setup_main_video(self):
        """Setup main/background video yang looping"""
        if not self.is_connected():
            print("Not connected to OBS!")
            return False
        
        if not self.main_video_path:
            print("⚠ No main video configured in config.json")
            return False
        
        main_video_file = Path(self.main_video_path)
        if not main_video_file.exists():
            print(f"⚠ Main video not found: {self.main_video_path}")
            print(f"  Please set a valid main_video_path in config.json")
            return False
        
        print(f"\n🎬 Setting up main background video...")
        print(f"   Video: {main_video_file.name}")
        
        try:
            sources = self.get_sources()
            
            # Create main video source if not exists
            if self.main_video_source not in sources:
                print(f"  → Creating main video source '{self.main_video_source}'...")
                if not self.create_media_source(
                    self.main_video_source, 
                    self.main_video_path, 
                    looping=True
                ):
                    print(f"  ✗ Failed to create main video source!")
                    return False
                print(f"  ✓ Main video source created!")
            else:
                # Update existing source
                self.update_media_source(
                    self.main_video_source, 
                    self.main_video_path, 
                    looping=True
                )
            
            # Start playing main video
            self.play_main_video()
            
            return True
            
        except Exception as e:
            print(f"✗ Error setting up main video: {e}")
            return False
    
    def play_main_video(self):
        """Play main/background video (looping)"""
        if not self.is_connected():
            return False
        
        if not self.main_video_path:
            return False
        
        try:
            # Hide promo video source
            if self.video_source_name in self.get_sources():
                self.set_source_visibility(self.video_source_name, False)
            
            # Show and restart main video
            self.set_source_visibility(self.main_video_source, True)
            
            self.ws.call(obs_requests.TriggerMediaInputAction(
                inputName=self.main_video_source,
                mediaAction='OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART'
            ))
            
            self.is_playing_promo = False
            print(f"✓ Main video playing (looping)")
            
            return True
            
        except Exception as e:
            print(f"Error playing main video: {e}")
            return False


if __name__ == "__main__":
    # Test
    print("=== OBS Controller Test ===\n")
    
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    controller = OBSController(config)
    
    if controller.connect():
        print("\nScenes available:")
        scenes = controller.get_scenes()
        for scene in scenes:
            print(f"  - {scene}")
        
        print("\nSources in current scene:")
        sources = controller.get_sources()
        for source in sources:
            print(f"  - {source}")
        
        input("\nPress Enter to disconnect...")
        controller.disconnect()
    else:
        print("\nFailed to connect to OBS.")
        print("Please check the setup instructions in README.md")
