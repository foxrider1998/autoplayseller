"""
AutoPlay Seller - Main Application
Aplikasi autoplay video untuk livestream jualan
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import time
from pathlib import Path
from datetime import datetime

from comment_detector import create_comment_detector, CommentMatcher, Comment
from obs_controller import OBSController
from config_editor import ConfigEditorWindow


class AutoPlaySellerApp:
    """Main application GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AutoPlay Seller - Livestream Auto Video Player")
        self.root.geometry("1000x700")
        
        # Load config
        self.config = self.load_config()
        
        # Initialize components
        self.obs_controller = OBSController(self.config)
        self.comment_detector = create_comment_detector(self.config)
        self.comment_matcher = CommentMatcher(self.config['comment_keywords'])
        
        # State
        self.running = False
        self.stats = {
            'total_comments': 0,
            'matched_comments': 0,
            'videos_played': 0,
            'start_time': None
        }
        
        # Setup GUI
        self.setup_gui()
        
        # Setup callbacks
        self.comment_detector.add_callback(self.on_comment_received)
        
    def load_config(self) -> dict:
        """Load configuration file"""
        config_path = Path("config.json")
        if not config_path.exists():
            messagebox.showerror("Error", "config.json not found!")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def setup_gui(self):
        """Setup GUI components"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Edit Config", command=self.edit_config)
        file_menu.add_command(label="Reload Config", command=self.reload_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # === Status Frame ===
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # OBS Status
        self.obs_status_label = ttk.Label(status_frame, text="OBS: Disconnected", 
                                         foreground="red", font=("", 10, "bold"))
        self.obs_status_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Detector Status
        self.detector_status_label = ttk.Label(status_frame, text="Detector: Stopped", 
                                              foreground="gray", font=("", 10, "bold"))
        self.detector_status_label.grid(row=0, column=1, sticky=tk.W, padx=20)
        
        # Current video
        self.current_video_label = ttk.Label(status_frame, text="Current: None", 
                                            font=("", 9))
        self.current_video_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(5, 0))
        
        # === Control Frame ===
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons - Row 1
        self.connect_btn = ttk.Button(control_frame, text="🔌 Auto Connect OBS", 
                                     command=self.connect_obs, width=20)
        self.connect_btn.grid(row=0, column=0, padx=5)
        
        self.reconnect_btn = ttk.Button(control_frame, text="🔄 Reconnect", 
                                       command=self.reconnect_obs, width=15, state='disabled')
        self.reconnect_btn.grid(row=0, column=1, padx=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Monitoring", 
                                    command=self.start_monitoring, 
                                    width=20, state='disabled')
        self.start_btn.grid(row=0, column=2, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop Monitoring", 
                                   command=self.stop_monitoring, 
                                   width=20, state='disabled')
        self.stop_btn.grid(row=0, column=3, padx=5)
        
        # Buttons - Row 2
        ttk.Button(control_frame, text="🎬 Test Video", 
                  command=self.test_video, width=15).grid(row=1, column=0, padx=5, pady=(5, 0))
        
        ttk.Button(control_frame, text="🔍 Detect Resources", 
                  command=self.detect_resources, width=15).grid(row=1, column=1, padx=5, pady=(5, 0))
        
        ttk.Button(control_frame, text="🗑️ Clear Log", 
                  command=self.clear_log, width=15).grid(row=1, column=2, padx=5, pady=(5, 0))
        
        # === Stats Frame ===
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, 
                                     text="Total: 0 | Matched: 0 | Videos: 0 | Runtime: 0:00:00",
                                     font=("", 9))
        self.stats_label.pack(anchor=tk.W)
        
        # === Log Frame ===
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, 
                                                  wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("comment", foreground="blue")
        
        # Initial log
        self.log("Application started", "info")
        self.log(f"Config loaded: {len(self.config['comment_keywords'])} keywords configured", "info")
    
    def log(self, message: str, level: str = "info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log text"""
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared", "info")
    
    def update_obs_status(self, connected: bool):
        """Update OBS connection status"""
        if connected:
            self.obs_status_label.config(text="OBS: Connected ✓", foreground="green")
        else:
            self.obs_status_label.config(text="OBS: Disconnected ✗", foreground="red")
    
    def update_detector_status(self, running: bool):
        """Update detector status"""
        if running:
            self.detector_status_label.config(text="Detector: Running ✓", foreground="green")
        else:
            self.detector_status_label.config(text="Detector: Stopped", foreground="gray")
    
    def update_stats_display(self):
        """Update statistics display"""
        runtime = "0:00:00"
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            runtime = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        text = (f"Total Comments: {self.stats['total_comments']} | "
                f"Matched: {self.stats['matched_comments']} | "
                f"Videos Played: {self.stats['videos_played']} | "
                f"Runtime: {runtime}")
        
        self.stats_label.config(text=text)
    
    def connect_obs(self):
        """Connect to OBS with auto-detection"""
        self.log("🔍 Auto-detecting OBS...", "info")
        
        # Try auto-connect first
        if self.obs_controller.auto_connect():
            self.log("✓ Connected to OBS successfully!", "success")
            
            # Show detected settings
            self.log(f"  Host: {self.obs_controller.host}", "info")
            self.log(f"  Port: {self.obs_controller.port}", "info")
            
            self.update_obs_status(True)
            self.start_btn.config(state='normal')
            self.connect_btn.config(state='disabled')
            self.reconnect_btn.config(state='normal')
            
            # Auto-detect scenes and sources
            self._detect_obs_resources()
        else:
            self.log("✗ Failed to connect to OBS", "error")
            self.log("Make sure OBS is running with WebSocket enabled", "warning")
            messagebox.showerror("Connection Failed", 
                               "Failed to connect to OBS.\n\n"
                               "Please ensure:\n"
                               "1. OBS Studio is running\n"
                               "2. WebSocket server is enabled:\n"
                               "   Tools → WebSocket Server Settings\n"
                               "3. Port is accessible (default: 4455)")
    
    def _detect_obs_resources(self):
        """Detect scenes and sources in OBS"""
        try:
            # Get scenes
            scenes = self.obs_controller.get_scenes()
            if scenes:
                self.log(f"  Found {len(scenes)} scene(s): {', '.join(scenes[:3])}", "info")
            
            # Get sources in current scene
            sources = self.obs_controller.get_sources()
            if sources:
                self.log(f"  Found {len(sources)} source(s) in current scene", "info")
                
                # Check if VideoPlayer exists
                if self.obs_controller.video_source_name not in sources:
                    self.log(f"  ⚠ Warning: '{self.obs_controller.video_source_name}' source not found!", "warning")
                    self.log(f"    Please create Media Source with name '{self.obs_controller.video_source_name}'", "info")
                else:
                    self.log(f"  ✓ '{self.obs_controller.video_source_name}' source found!", "success")
        except Exception as e:
            self.log(f"  Error detecting resources: {e}", "warning")
    
    def reconnect_obs(self):
        """Reconnect to OBS"""
        self.log("Reconnecting to OBS...", "info")
        
        # Disconnect first
        if self.obs_controller.is_connected():
            self.obs_controller.disconnect()
            self.update_obs_status(False)
        
        # Try to reconnect
        time.sleep(0.5)
        self.connect_obs()
    
    def detect_resources(self):
        """Manually detect OBS resources"""
        if not self.obs_controller.is_connected():
            messagebox.showwarning("Not Connected", 
                                 "Please connect to OBS first!")
            return
        
        self.log("🔍 Detecting OBS resources...", "info")
        self._detect_obs_resources()
    
    def start_monitoring(self):
        """Start comment monitoring"""
        self.running = True
        self.stats['start_time'] = time.time()
        
        self.comment_detector.start()
        self.update_detector_status(True)
        
        self.log("Started monitoring comments", "success")
        
        # Update buttons
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.connect_btn.config(state='disabled')
        
        # Start update loop
        self.update_loop()
    
    def stop_monitoring(self):
        """Stop comment monitoring"""
        self.running = False
        
        self.comment_detector.stop()
        self.update_detector_status(False)
        
        self.log("Stopped monitoring comments", "warning")
        
        # Update buttons
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
    
    def update_loop(self):
        """Main update loop"""
        if self.running:
            # Update comment detector
            self.comment_detector.update()
            
            # Update stats display
            self.update_stats_display()
            
            # Schedule next update
            self.root.after(500, self.update_loop)
    
    def on_comment_received(self, comment: Comment):
        """Callback when new comment is received"""
        self.stats['total_comments'] += 1
        
        self.log(f"💬 New comment: {comment.username}: {comment.text}", "comment")
        
        # Try to match with keywords
        match_result = self.comment_matcher.match(comment)
        
        if match_result:
            self.stats['matched_comments'] += 1
            keyword = match_result['matched_keyword']
            video_path = match_result['video_path']
            response = match_result['response_text']
            
            self.log(f"  ✓ Matched keyword: '{keyword}'", "success")
            self.log(f"  📹 Playing video: {video_path}", "info")
            
            # Play video
            if self.obs_controller.play_video(video_path):
                self.stats['videos_played'] += 1
                self.current_video_label.config(text=f"Current: {Path(video_path).name}")
                self.log(f"  ✓ Video playing!", "success")
                
                # Auto-hide after duration (optional)
                if self.config['video_settings'].get('auto_hide_after_play', True):
                    duration = self.obs_controller.get_media_duration()
                    if duration > 0:
                        # Schedule hide after video finishes
                        self.root.after(int(duration * 1000) + 500, 
                                       lambda: self.obs_controller.stop_video())
            else:
                self.log(f"  ✗ Failed to play video!", "error")
        else:
            self.log(f"  No matching keyword found", "info")
        
        self.update_stats_display()
    
    def test_video(self):
        """Test video playback"""
        if not self.obs_controller.is_connected():
            messagebox.showwarning("Not Connected", "Please connect to OBS first")
            return
        
        # Get first video from config
        keywords = self.config['comment_keywords']
        if not keywords:
            messagebox.showwarning("No Videos", "No videos configured in config.json")
            return
        
        first_keyword = list(keywords.keys())[0]
        video_path = keywords[first_keyword]['video_path']
        
        self.log(f"Testing video: {video_path}", "info")
        
        if self.obs_controller.play_video(video_path):
            self.log("✓ Test video playing!", "success")
            messagebox.showinfo("Success", f"Test video is now playing!\n\n{video_path}")
        else:
            self.log("✗ Failed to play test video", "error")
            messagebox.showerror("Error", "Failed to play test video.\n"
                               "Check if the video file exists.")
    
    def edit_config(self):
        """Open config editor window"""
        self.log("Opening config editor...", "info")
        
        def on_save(new_config):
            """Callback when config is saved"""
            self.log("Configuration updated from editor", "success")
        
        # Open config editor window
        editor = ConfigEditorWindow(self.root, self.config, on_save_callback=on_save)
    
    def reload_config(self):
        """Reload configuration"""
        self.log("Reloading configuration...", "info")
        
        try:
            self.config = self.load_config()
            self.comment_matcher = CommentMatcher(self.config['comment_keywords'])
            self.log(f"✓ Config reloaded: {len(self.config['comment_keywords'])} keywords", "success")
            messagebox.showinfo("Success", "Configuration reloaded successfully!")
        except Exception as e:
            self.log(f"✗ Failed to reload config: {e}", "error")
            messagebox.showerror("Error", f"Failed to reload config:\n{e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """AutoPlay Seller v1.0

Aplikasi autoplay video untuk livestream jualan
Compatible dengan TikTok Shop, Shopee, dan platform lainnya

Fitur:
• Deteksi komentar otomatis (keranjang 1-100)
• Integrasi dengan OBS Studio
• Konfigurasi video dan response yang fleksibel
• Monitoring real-time

Dibuat dengan Python + OBS WebSocket
"""
        messagebox.showinfo("About", about_text)
    
    def on_closing(self):
        """Handle window closing"""
        if self.running:
            if messagebox.askokcancel("Quit", "Monitoring is still running. Stop and quit?"):
                self.stop_monitoring()
                if self.obs_controller.is_connected():
                    self.obs_controller.disconnect()
                self.root.destroy()
        else:
            if self.obs_controller.is_connected():
                self.obs_controller.disconnect()
            self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AutoPlaySellerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
