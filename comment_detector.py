"""
Comment Detector Module
Mendeteksi komentar dari berbagai sumber (file, API, dll)
"""
import time
import json
import re
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import subprocess
import threading
from queue import Queue, Empty
import socketio

from tiktok_api import fetch_video_comments, TikTokAPIError

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.types.events import CommentEvent
except Exception:
    TikTokLiveClient = None  # Will validate at runtime


class Comment:
    """Representasi data komentar"""
    def __init__(self, username: str, text: str, timestamp: str = None):
        self.username = username
        self.text = text.lower().strip()
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def __str__(self):
        return f"[{self.timestamp}] {self.username}: {self.text}"


class CommentDetector:
    """Base class untuk mendeteksi komentar"""
    def __init__(self, config: Dict):
        self.config = config
        self.callbacks: List[Callable] = []
        self.processed_comments = set()
    
    def add_callback(self, callback: Callable):
        """Tambah callback yang akan dipanggil saat ada komentar baru"""
        self.callbacks.append(callback)
    
    def notify_callbacks(self, comment: Comment):
        """Panggil semua callback dengan komentar baru"""
        for callback in self.callbacks:
            try:
                callback(comment)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def start(self):
        """Mulai monitoring komentar"""
        raise NotImplementedError
    
    def stop(self):
        """Stop monitoring komentar"""
        raise NotImplementedError

    def get_new_comments(self) -> List["Comment"]:
        """Return list komentar baru sejak panggilan terakhir"""
        raise NotImplementedError

    def get_new_comments(self) -> List["Comment"]:
    	"""Kembalikan list komentar baru sejak panggilan terakhir"""
    	raise NotImplementedError


class FileCommentDetector(CommentDetector):
    """Deteksi komentar dari file teks"""
    def __init__(self, config: Dict):
        super().__init__(config)
        self.file_path = Path(config['comment_source']['file_path'])
        self.check_interval = config['comment_source'].get('check_interval', 1.0)
        self.running = False
        self.last_position = 0
        
        # Buat file jika belum ada
        if not self.file_path.exists():
            self.file_path.touch()
    
    def parse_comment_line(self, line: str) -> Optional[Comment]:
        """Parse baris komentar dari file"""
        line = line.strip()
        if not line:
            return None
        
        # Format: [timestamp] username: comment
        pattern = r'\[(.+?)\]\s*(.+?):\s*(.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, username, text = match.groups()
            return Comment(username, text, timestamp)
        else:
            # Format sederhana: username: comment
            simple_pattern = r'(.+?):\s*(.+)'
            simple_match = re.match(simple_pattern, line)
            if simple_match:
                username, text = simple_match.groups()
                return Comment(username, text)
        
        return None
    
    def check_new_comments(self):
        """Check file untuk komentar baru"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # Pindah ke posisi terakhir yang dibaca
                f.seek(self.last_position)
                
                # Baca baris baru
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                # Parse dan notify
                for line in new_lines:
                    comment = self.parse_comment_line(line)
                    if comment:
                        comment_id = f"{comment.username}:{comment.text}:{comment.timestamp}"
                        if comment_id not in self.processed_comments:
                            self.processed_comments.add(comment_id)
                            self.notify_callbacks(comment)
        except Exception as e:
            print(f"Error reading comments file: {e}")

    def get_new_comments(self) -> List["Comment"]:
        """Return list komentar baru tanpa callbacks (untuk web server loop)"""
        new_comments: List[Comment] = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                for line in new_lines:
                    comment = self.parse_comment_line(line)
                    if comment:
                        comment_id = f"{comment.username}:{comment.text}:{comment.timestamp}"
                        if comment_id not in self.processed_comments:
                            self.processed_comments.add(comment_id)
                            new_comments.append(comment)
        except Exception as e:
            print(f"Error reading comments file: {e}")
        return new_comments

    def get_new_comments(self) -> List["Comment"]:
        """Return list komentar baru tanpa menggunakan callbacks"""
        new_comments: List[Comment] = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                for line in new_lines:
                    comment = self.parse_comment_line(line)
                    if comment:
                        comment_id = f"{comment.username}:{comment.text}:{comment.timestamp}"
                        if comment_id not in self.processed_comments:
                            self.processed_comments.add(comment_id)
                            new_comments.append(comment)
        except Exception as e:
            print(f"Error reading comments file: {e}")
        return new_comments
    
    def start(self):
        """Mulai monitoring file"""
        self.running = True
        # Set posisi awal ke akhir file
        if self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # Seek to end
                self.last_position = f.tell()
        
        print(f"Monitoring komentar dari: {self.file_path}")
    
    def stop(self):
        """Stop monitoring file"""
        self.running = False
        print("Stopped monitoring comments")
    
    def update(self):
        """Update method yang dipanggil secara berkala"""
        if self.running:
            self.check_new_comments()


class TikTokCommentDetector(CommentDetector):
    """Deteksi komentar langsung dari TikTok Research API"""
    def __init__(self, config: Dict):
        super().__init__(config)
        src = config.get('comment_source', {})
        self.src = src
        self.video_id = src.get('video_id')
        if self.video_id is None:
            raise ValueError("comment_source.video_id is required for TikTok")
        self.fields = src.get('fields', 'id,text,like_count,reply_count,create_time,video_id,parent_comment_id')
        self.max_count = int(src.get('max_count', 10))
        self.cursor = int(src.get('cursor', 0))
        self.poll_interval = float(src.get('poll_interval', 2.0))
        self.running = False
        self._last_poll = 0.0

    def start(self):
        self.running = True
        self._last_poll = 0.0
        print(f"Monitoring TikTok comments for video_id={self.video_id}")

    def stop(self):
        self.running = False
        print("Stopped TikTok comments monitoring")

    def _to_comment(self, item: Dict) -> Optional[Comment]:
        text = item.get('text', '')
        if not text:
            return None
        # TikTok response does not include username; use a placeholder
        username = f"tiktok:{item.get('id', 'unknown')}"
        ts = item.get('create_time')
        if isinstance(ts, int):
            # convert unix timestamp to readable string
            try:
                dt = datetime.fromtimestamp(ts)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp = None
        else:
            timestamp = None
        return Comment(username=username, text=text, timestamp=timestamp)

    def fetch_and_notify(self):
        try:
            result = fetch_video_comments(
                self.src,
                video_id=self.video_id,
                fields=self.fields,
                max_count=self.max_count,
                cursor=self.cursor,
            )
        except TikTokAPIError as e:
            print(f"TikTok API error: {e}")
            return

        comments = result.get('comments', [])
        # Update cursor for next page, but do not exceed 1000
        self.cursor = int(result.get('cursor', self.cursor))

        for item in comments:
            comment = self._to_comment(item)
            if not comment:
                continue
            # Use TikTok comment id to deduplicate
            comment_id = f"tiktok:{item.get('id')}"
            if comment_id not in self.processed_comments:
                self.processed_comments.add(comment_id)
                self.notify_callbacks(comment)

    def get_new_comments(self) -> List["Comment"]:
        """Return list komentar baru dari TikTok tanpa callbacks"""
        out: List[Comment] = []
        try:
            result = fetch_video_comments(
                self.src,
                video_id=self.video_id,
                fields=self.fields,
                max_count=self.max_count,
                cursor=self.cursor,
            )
        except TikTokAPIError as e:
            print(f"TikTok API error: {e}")
            return out

        comments = result.get('comments', [])
        self.cursor = int(result.get('cursor', self.cursor))
        for item in comments:
            comment = self._to_comment(item)
            if not comment:
                continue
            cid = f"tiktok:{item.get('id')}"
            if cid not in self.processed_comments:
                self.processed_comments.add(cid)
                out.append(comment)
        return out

    def update(self):
        if not self.running:
            return
        now = time.time()
        if now - self._last_poll >= self.poll_interval:
            self._last_poll = now
            self.fetch_and_notify()

    def get_new_comments(self) -> List["Comment"]:
        """Return list komentar baru dari TikTok tanpa callbacks"""
        out: List[Comment] = []
        try:
            result = fetch_video_comments(
                self.src,
                video_id=self.video_id,
                fields=self.fields,
                max_count=self.max_count,
                cursor=self.cursor,
            )
        except TikTokAPIError as e:
            print(f"TikTok API error: {e}")
            return out

        comments = result.get('comments', [])
        self.cursor = int(result.get('cursor', self.cursor))
        for item in comments:
            comment = self._to_comment(item)
            if not comment:
                continue
            cid = f"tiktok:{item.get('id')}"
            if cid not in self.processed_comments:
                self.processed_comments.add(cid)
                out.append(comment)
        return out


class DummyTikTokCommentDetector(CommentDetector):
    """Dummy detector that emits example comments at a fixed interval."""
    def __init__(self, config: Dict):
        super().__init__(config)
        src = config.get('comment_source', {})
        self.poll_interval = float(src.get('poll_interval', 1.0))
        self.running = False
        self._last_emit = 0.0
        self._counter = 0
        # Example texts simulating typical live comments
        self._samples = [
            "keranjang 1",
            "keranjang 2",
            "keranjang 3",
            "mau keranjang 1",
            "mau keranjang 2 dong",
            "masukin keranjang 3",
            "keranjang1",
            "krnjg 2",
        ]

    def start(self):
        self.running = True
        self._last_emit = 0.0
        print("Monitoring dummy TikTok comments (example mode)")

    def stop(self):
        self.running = False
        print("Stopped dummy TikTok comments monitoring")

    def _make_comment(self) -> Comment:
        import random, time as _t
        self._counter += 1
        text = random.choice(self._samples)
        ts = datetime.fromtimestamp(int(_t.time())).strftime("%Y-%m-%d %H:%M:%S")
        return Comment(username=f"dummy:{self._counter}", text=text, timestamp=ts)

    def get_new_comments(self) -> List["Comment"]:
        out: List[Comment] = []
        now = time.time()
        # Emit at most one comment per poll interval
        if now - self._last_emit >= self.poll_interval:
            self._last_emit = now
            c = self._make_comment()
            cid = f"dummy:{self._counter}"
            if cid not in self.processed_comments:
                self.processed_comments.add(cid)
                out.append(c)
        return out

    def update(self):
        # Not used in polling loop, kept for API symmetry
        pass


class TikTokLiveConnectorDetector(CommentDetector):
    """Use Node-based TikTok-Live-Connector to stream live comments.

    Spawns a Node process running node_bridge/tiktok_live_bridge.js and reads JSON lines
    for chat events, converting them to Comment instances consumable by the server loop.
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        src = config.get('comment_source', {})
        self.username = src.get('live_username') or src.get('username') or ''
        if not self.username:
            raise ValueError("comment_source.live_username is required for tiktok_live")
        self.poll_interval = float(src.get('poll_interval', 1.0))
        self.bridge_path = src.get('bridge_path', str(Path('node_bridge') / 'tiktok_live_bridge.js'))
        self.proc: Optional[subprocess.Popen] = None
        self.queue: "Queue[Comment]" = Queue()
        self.running = False
        self._reader_thread: Optional[threading.Thread] = None

    def _reader(self, stream):
        for line in iter(stream.readline, ''):
            try:
                data = json.loads(line.strip())
                if data.get('type') == 'comment':
                    text = (data.get('comment') or '').strip()
                    if not text:
                        continue
                    user = data.get('user', {})
                    username = user.get('nickname') or user.get('uniqueId') or 'tiktok'
                    ts = data.get('timestamp')
                    if isinstance(ts, (int, float)):
                        try:
                            timestamp = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            timestamp = None
                    else:
                        timestamp = None
                    c = Comment(username=username, text=text, timestamp=timestamp)
                    cid = data.get('msgId') or f"{username}:{text}:{timestamp}"
                    if cid in self.processed_comments:
                        continue
                    self.processed_comments.add(cid)
                    self.queue.put(c)
            except Exception:
                continue

    def start(self):
        if self.running:
            return
        self.running = True
        cmd = ["node", self.bridge_path, "--uniqueId", self.username]
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except FileNotFoundError:
            raise RuntimeError("Node.js not found. Please install Node.js to use TikTok-Live-Connector.")
        if not self.proc or not self.proc.stdout:
            raise RuntimeError("Failed to start TikTok live bridge process")
        self._reader_thread = threading.Thread(target=self._reader, args=(self.proc.stdout,), daemon=True)
        self._reader_thread.start()
        print(f"Monitoring TikTok Live comments for @{self.username}")

    def stop(self):
        self.running = False
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass
        self.proc = None

    def get_new_comments(self) -> List["Comment"]:
        out: List[Comment] = []
        while True:
            try:
                out.append(self.queue.get_nowait())
            except Empty:
                break
        return out

class TikTokSocketIODetector(CommentDetector):
    """Connects to an external Socket.IO server that proxies TikTok live events.

    Expects the external server to accept 'setUniqueId' with (uniqueId, options)
    and emit 'chat' events containing at least { comment, uniqueId|nickname }.
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        src = config.get('comment_source', {})
        self.server_url = src.get('server_url', 'http://localhost:8081')
        self.username = src.get('live_username') or src.get('username') or ''
        if not self.username:
            raise ValueError("comment_source.live_username is required for tiktok_live_socket")
        self._client = socketio.Client(logger=False, engineio_logger=False)
        self.queue: "Queue[Comment]" = Queue()
        self.running = False

        @self._client.event
        def connect():
            try:
                self._client.emit('setUniqueId', self.username, {})
            except Exception:
                pass

        @self._client.event
        def chat(msg):
            try:
                text = (msg.get('comment') or '').strip()
                if not text:
                    return
                nickname = msg.get('nickname') or msg.get('user', {}).get('nickname')
                unique_id = msg.get('uniqueId') or msg.get('user', {}).get('uniqueId')
                uname = nickname or unique_id or 'tiktok'
                c = Comment(username=uname, text=text)
                cid = msg.get('msgId') or f"{uname}:{text}:{c.timestamp}"
                if cid in self.processed_comments:
                    return
                self.processed_comments.add(cid)
                self.queue.put(c)
            except Exception:
                return

        @self._client.event
        def disconnect():
            pass

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            self._client.connect(self.server_url, wait=True)
            print(f"Connected to external Socket.IO at {self.server_url} for @{self.username}")
        except Exception as e:
            self.running = False
            raise RuntimeError(f"Failed to connect to {self.server_url}: {e}")

    def stop(self):
        self.running = False
        try:
            if self._client.connected:
                self._client.disconnect()
        except Exception:
            pass

    def get_new_comments(self) -> List["Comment"]:
        out: List[Comment] = []
        while True:
            try:
                out.append(self.queue.get_nowait())
            except Empty:
                break
        return out

class TikTokLivePyDetector(CommentDetector):
    """Use the Python TikTokLive library to stream live comments.

    Runs a TikTokLiveClient in a background thread and enqueues Comment objects.
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        src = config.get('comment_source', {})
        self.username = src.get('live_username') or src.get('username') or ''
        if not self.username:
            raise ValueError("comment_source.live_username is required for tiktok_live_py")
        if TikTokLiveClient is None:
            raise RuntimeError("TikTokLive package not installed. Run: pip install TikTokLive")
        self.queue: "Queue[Comment]" = Queue()
        self.client = TikTokLiveClient(unique_id=self.username)
        self._thread: Optional[threading.Thread] = None
        self.running = False
        self._backoff = 1.0  # seconds, grows on failures

        @self.client.on("comment")
        async def on_comment(event: CommentEvent):
            try:
                text = (event.comment or '').strip()
                if not text:
                    return
                uname = getattr(event.user, 'nickname', None) or getattr(event.user, 'uniqueId', None) or 'tiktok'
                c = Comment(username=uname, text=text)
                cid = getattr(event, 'msg_id', None) or f"{uname}:{text}:{c.timestamp}"
                if cid in self.processed_comments:
                    return
                self.processed_comments.add(cid)
                self.queue.put(c)
            except Exception:
                return

    def _run(self):
        while self.running:
            try:
                self.client.run()
                # If run() returns, break loop unless stopped
                if not self.running:
                    break
            except Exception:
                # Simple reconnect with backoff
                try:
                    time.sleep(self._backoff)
                except Exception:
                    pass
                self._backoff = min(self._backoff * 2, 30.0)
                continue
            # Reset backoff on clean loop
            self._backoff = 1.0

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"Monitoring TikTok Live (Python) for @{self.username}")

    def stop(self):
        self.running = False
        try:
            self.client.stop()
        except Exception:
            pass

    def get_new_comments(self) -> List["Comment"]:
        out: List[Comment] = []
        while True:
            try:
                out.append(self.queue.get_nowait())
            except Empty:
                break
        return out

class CommentMatcher:
    """Match komentar dengan keyword configuration"""
    def __init__(self, keywords_config: Dict):
        self.keywords_config = keywords_config
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns untuk setiap keyword"""
        patterns = {}
        for keyword, config in self.keywords_config.items():
            # Check if this keyword is a regex pattern
            is_regex = config.get('is_regex', False)
            
            if is_regex:
                # Use keyword as-is as regex pattern
                try:
                    pattern = re.compile(keyword, re.IGNORECASE)
                    patterns[keyword] = pattern
                except re.error as e:
                    print(f"Warning: Invalid regex pattern '{keyword}': {e}")
                    # Fallback to literal match
                    keyword_clean = re.escape(keyword.lower())
                    pattern = re.compile(r'\b' + keyword_clean + r'\b', re.IGNORECASE)
                    patterns[keyword] = pattern
            else:
                # Create pattern yang match keyword (case insensitive)
                # Support "keranjang 1", "krnjg 1", "keranjang1", dll
                keyword_clean = keyword.lower().replace(" ", r"\s*")
                pattern = re.compile(r'\b' + keyword_clean + r'\b', re.IGNORECASE)
                patterns[keyword] = pattern
        
        return patterns
    
    def match(self, comment: Comment) -> Optional[Dict]:
        """Match komentar dengan configuration"""
        comment_text = comment.text.lower()
        
        # Cek setiap pattern
        for keyword, pattern in self.patterns.items():
            if pattern.search(comment_text):
                config = self.keywords_config[keyword].copy()
                config['matched_keyword'] = keyword
                config['comment'] = comment
                return config
        
        return None

    def find_match(self, text: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Match plain text dan return (keyword, config)"""
        text_l = (text or '').lower()
        for keyword, pattern in self.patterns.items():
            if pattern.search(text_l):
                cfg = self.keywords_config[keyword].copy()
                return keyword, cfg
        return None, None

    def find_match(self, text: str):
        """Compatibility: return (keyword, config) by matching plain text"""
        text_l = (text or '').lower()
        for keyword, pattern in self.patterns.items():
            if pattern.search(text_l):
                cfg = self.keywords_config[keyword].copy()
                return keyword, cfg
        return None, None

    def find_all_matches(self, text: str) -> List[Tuple[str, Dict]]:
        """Return all matching (keyword, config) pairs for the given text."""
        text_l = (text or '').lower()
        matches: List[Tuple[str, Dict]] = []
        for keyword, pattern in self.patterns.items():
            if pattern.search(text_l):
                cfg = self.keywords_config[keyword].copy()
                matches.append((keyword, cfg))
        return matches


def create_comment_detector(config: Dict) -> CommentDetector:
    """Factory function untuk membuat comment detector"""
    source_type = config['comment_source']['type']
    
    if source_type == 'file':
        return FileCommentDetector(config)
    elif source_type == 'tiktok':
        return TikTokCommentDetector(config)
    elif source_type == 'tiktok_dummy':
        return DummyTikTokCommentDetector(config)
    elif source_type == 'tiktok_live':
        return TikTokLiveConnectorDetector(config)
    elif source_type == 'tiktok_live_socket':
        return TikTokSocketIODetector(config)
    elif source_type == 'tiktok_live_py':
        return TikTokLivePyDetector(config)
    else:
        raise ValueError(f"Unknown comment source type: {source_type}")


if __name__ == "__main__":
    # Test
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    detector = create_comment_detector(config)
    matcher = CommentMatcher(config['comment_keywords'])
    
    def on_comment(comment: Comment):
        print(f"New comment: {comment}")
        match_result = matcher.match(comment)
        if match_result:
            print(f"  -> Matched: {match_result['matched_keyword']}")
            print(f"  -> Video: {match_result['video_path']}")
            print(f"  -> Response: {match_result['response_text']}")
        else:
            print("  -> No match")
    
    detector.add_callback(on_comment)
    detector.start()
    
    print("Monitoring comments... (Ctrl+C to stop)")
    try:
        while True:
            detector.update()
            time.sleep(0.5)
    except KeyboardInterrupt:
        detector.stop()
        print("\nStopped")
