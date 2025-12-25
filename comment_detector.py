"""
Comment Detector Module
Mendeteksi komentar dari berbagai sumber (file, API, dll)
"""
import time
import json
import re
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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


def create_comment_detector(config: Dict) -> CommentDetector:
    """Factory function untuk membuat comment detector"""
    source_type = config['comment_source']['type']
    
    if source_type == 'file':
        return FileCommentDetector(config)
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
